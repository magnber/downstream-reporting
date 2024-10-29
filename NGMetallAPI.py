from dataclasses import dataclass, asdict
from typing import List, Dict
import csv
import json

### Data models:
@dataclass
class Material:
    code: str
    description: str

@dataclass
class Facility:
    id: str
    name: str
    location: str

# MaterialTransformation represents is a mapping of input to output materials. From a production perspective this is similar to a BOM (bill of materials)
# Each input material mapped to one or more output materials. 
# Yield is the fraction of output_material we get from an input material - this should sum to 1 (or 100%)
# Category us the category of the output material. 
# Category is what we ultimately want to report on to the customer, but the output material dist is needed to calculate the generated emissions a recycled metal creates.
@dataclass
class MaterialTransformation:
    facility_id: str
    input_material_code: str # one line per input material
    output_material_code: str # the output material
    percentage: float # a group on input_material should sum percentage to 1 (100%)
    category: str  # 'Material Recycling', 'Energy Recycling', 'Losses'

# Emission factor per material per facility - denoted in kg CO2e used per tonn processed
@dataclass
class EmissionFactorProcessing:
    facility_id: str
    material_code: str
    emission_factor: float  # kg CO2e per tonne processed

# estimated geografical downstream output per material code - what countries buys our goods?
# one output material can be sold to multiple countries - group on output_material_code sum percentage should be 1 (or 100%).
@dataclass
class EstimatedOutputDistributionGeo:
    output_material_code: str
    destination_country: str
    percentage: float  # The percentage that goes to one specific country. A group on output_material_code should sum this to 1 (100%)

# Factors for transportation emissions per type of transport
@dataclass
class TransportEmissionFactor:
    mode_of_transport: str
    emission_factor: float  # kg CO2e per tonne-km

# Average for downstream - used to calculate distances from facilites to downstream customers / countries
@dataclass
class AverageDownstreamDistances:
    facility_id: str
    destination_country: str
    average_distance: float  # km
    mode_of_transport: str

# Average distance for upstream - used to calculate distances from customers to facilites
@dataclass
class AverageUpstreamDistances:
    customer_id: str
    facility_id: str
    inbound_average_distance: float  # km
    inbound_mode_of_transport: str

# benchmarks for virgin produced metals
@dataclass
class VirginMaterialProductionBenchmark:
    material_code: str
    emissions: float  # kg CO2e per tonne produced

# Lookup / aggregation for countries to region
@dataclass
class GeographicRegion:
    country: str
    region: str

# Customer invoice - input data
@dataclass
class Invoice:
    invoice_id: str
    customer_id: str
    delivery_date: str
    facility_id: str
    material_code: str
    volume: float

# output data
@dataclass
class RecyclingReport:
    invoice_id: str # The invoice the report is calculated from
    customer_id: str
    delivery_date: str
    facility_id: str
    input_material_code: str # received material
    output_material_code: str # the output material 
    category: str # the output material category
    volume_delivered: float # the volume of the input material
    output_volume: float # volume of the output material
    processing_emissions: float # processing emissions attributed to the output material (kg co2e)
    inbound_transport_emissions: float # transport emission from upstream to facility (kg co2e)
    outbound_transport_emissions: float # transport emission from facility to downstream customer (kg co2e)
    total_transport_emissions: float # sum emissions
    production_benchmark_emissions: float # Benchmark for output material 
    destination_country: str # country the output is sold to
    destination_volume: float # the percent out the output that is shipped to this country * the output_volume


class NGMetallAPI:
    def __init__(self):
        # Load data from CSV files into data structures
        self.materials = self.load_csv('data/Material.csv', Material)
        self.facilities = self.load_csv('data/Facility.csv', Facility)
        self.material_transformations = self.load_csv('data/MaterialTransformation.csv', MaterialTransformation)
        self.emission_factors = self.load_csv('data/EmissionFactorProcessing.csv', EmissionFactorProcessing)
        self.output_distribution = self.load_csv('data/EstimatedOutputDistributionGeo.csv', EstimatedOutputDistributionGeo)
        self.transport_emission_factors = self.load_csv('data/TransportEmissionFactor.csv', TransportEmissionFactor)
        self.downstream_distances = self.load_csv('data/AverageDownstreamDistances.csv', AverageDownstreamDistances)
        self.upstream_distances = self.load_csv('data/AverageUpstreamDistances.csv', AverageUpstreamDistances)
        self.virgin_benchmarks = self.load_csv('data/VirginMaterialProductionBenchmark.csv', VirginMaterialProductionBenchmark)
        self.geographic_regions = self.load_csv('data/GeographicRegion.csv', GeographicRegion)
        self.index_data()

    def load_csv(self, filename, dataclass_type):
        data = []
        try:
            with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                field_types = dataclass_type.__annotations__
                for row in reader:
                    for key, value in row.items():
                        if key in field_types:
                            desired_type = field_types[key]
                            if desired_type == float:
                                row[key] = float(value)
                            elif desired_type == int:
                                row[key] = int(value)
                            # Leave strings as they are
                    data.append(dataclass_type(**row))
        except FileNotFoundError:
            print(f"File {filename} not found.")
        return data

    def index_data(self):
        # Create indexes for quick lookup
        self.material_transformation_index = {}
        for mt in self.material_transformations:
            key = (mt.facility_id, mt.input_material_code)
            self.material_transformation_index.setdefault(key, []).append(mt)

        self.emission_factor_index = {}
        for ef in self.emission_factors:
            key = (ef.facility_id, ef.material_code)
            self.emission_factor_index[key] = ef.emission_factor

        self.transport_emission_factor_index = {tef.mode_of_transport: tef.emission_factor for tef in self.transport_emission_factors}

        self.upstream_distance_index = {}
        for ud in self.upstream_distances:
            key = (ud.customer_id, ud.facility_id)
            self.upstream_distance_index[key] = ud

        self.downstream_distance_index = {}
        for dd in self.downstream_distances:
            key = (dd.facility_id, dd.destination_country)
            self.downstream_distance_index[key] = dd

        self.output_distribution_index = {}
        for od in self.output_distribution:
            self.output_distribution_index.setdefault(od.output_material_code, []).append(od)

        self.virgin_benchmark_index = {vb.material_code: vb.emissions for vb in self.virgin_benchmarks}

    def calculate_recycling_report(self, invoices: List[Invoice]) -> List[RecyclingReport]:
        reports = []
        for invoice in invoices:
            # Calculate output volumes
            transformations = self.get_material_transformations(invoice.facility_id, invoice.material_code)
            if not transformations:
                continue  # No transformation available
            output_volumes = self.calculate_output_volumes(invoice.volume, transformations)
            total_output_volume = sum(output_volumes.values())

            # Calculate processing emissions
            processing_emissions = self.calculate_processing_emissions(invoice.facility_id, invoice.material_code, invoice.volume)
            processing_emissions_allocated = self.allocate_emissions(processing_emissions, output_volumes)

            # Calculate inbound transport emissions
            inbound_emissions = self.calculate_inbound_transport_emissions(invoice.customer_id, invoice.facility_id, invoice.volume)
            inbound_emissions_allocated = self.allocate_emissions(inbound_emissions, output_volumes)

            for mt in transformations:
                output_volume = output_volumes[mt.output_material_code]
                processing_emission = processing_emissions_allocated[mt.output_material_code]
                inbound_emission = inbound_emissions_allocated[mt.output_material_code]
                total_transport_emission = inbound_emission

                if mt.category == 'Material Recycling':
                    # Calculate outbound transport emissions
                    output_distributions = self.get_output_distribution(mt.output_material_code)
                    for od in output_distributions:
                        destination_volume = output_volume * od.percentage
                        downstream_distance = self.get_downstream_distance(invoice.facility_id, od.destination_country)
                        if not downstream_distance:
                            continue
                        outbound_emission = destination_volume * downstream_distance.average_distance * self.transport_emission_factor_index.get(downstream_distance.mode_of_transport, 0)
                        total_transport_emission = inbound_emission + outbound_emission
                        benchmark_emission = self.virgin_benchmark_index.get(mt.output_material_code, 0) * destination_volume
                        report = RecyclingReport(
                            invoice_id=invoice.invoice_id,
                            customer_id=invoice.customer_id,
                            delivery_date=invoice.delivery_date,
                            facility_id=invoice.facility_id,
                            input_material_code=invoice.material_code,
                            output_material_code=mt.output_material_code,
                            category=mt.category,
                            volume_delivered=invoice.volume,
                            output_volume=output_volume,
                            processing_emissions=processing_emission,
                            inbound_transport_emissions=inbound_emission,
                            outbound_transport_emissions=outbound_emission,
                            total_transport_emissions=total_transport_emission,
                            production_benchmark_emissions=benchmark_emission,
                            destination_country=od.destination_country,
                            destination_volume=destination_volume
                        )
                        reports.append(report)
                else:
                    # Categories without downstream emissions
                    report = RecyclingReport(
                        invoice_id=invoice.invoice_id,
                        customer_id=invoice.customer_id,
                        delivery_date=invoice.delivery_date,
                        facility_id=invoice.facility_id,
                        input_material_code=invoice.material_code,
                        output_material_code=mt.output_material_code,
                        category=mt.category,
                        volume_delivered=invoice.volume,
                        output_volume=output_volume,
                        processing_emissions=processing_emission,
                        inbound_transport_emissions=inbound_emission,
                        outbound_transport_emissions=0.0,
                        total_transport_emissions=total_transport_emission,
                        production_benchmark_emissions=0.0,
                        destination_country='N/A',
                        destination_volume=output_volume
                    )
                    reports.append(report)
        return reports

    def get_material_transformations(self, facility_id, input_material_code):
        return self.material_transformation_index.get((facility_id, input_material_code), [])

    def calculate_output_volumes(self, volume_delivered, transformations):
        output_volumes = {}
        for mt in transformations:
            output_volume = volume_delivered * mt.percentage
            output_volumes[mt.output_material_code] = output_volume
        return output_volumes

    def calculate_processing_emissions(self, facility_id, material_code, volume_delivered):
        emission_factor = self.emission_factor_index.get((facility_id, material_code), 0)
        return volume_delivered * emission_factor

    def allocate_emissions(self, total_emissions, output_volumes):
        total_volume = sum(output_volumes.values())
        allocations = {}
        for code, volume in output_volumes.items():
            allocations[code] = (volume / total_volume) * total_emissions if total_volume else 0
        return allocations

    def calculate_inbound_transport_emissions(self, customer_id, facility_id, volume_delivered):
        upstream_distance = self.upstream_distance_index.get((customer_id, facility_id))
        if not upstream_distance:
            return 0
        emission_factor = self.transport_emission_factor_index.get(upstream_distance.inbound_mode_of_transport, 0)
        return volume_delivered * upstream_distance.inbound_average_distance * emission_factor

    def get_output_distribution(self, output_material_code):
        return self.output_distribution_index.get(output_material_code, [])

    def get_downstream_distance(self, facility_id, destination_country):
        return self.downstream_distance_index.get((facility_id, destination_country))



if __name__ == "__main__":
    api = NGMetallAPI()
    invoices = [Invoice(invoice_id='INV001', customer_id='Supplier001', delivery_date='2023-10-01', facility_id='F001', material_code='M001', volume=6000.0)]
    reports = api.calculate_recycling_report(invoices)

    reports_dict = [asdict(report) for report in reports]
    with open('output/recycling_reports.json', 'w', encoding='utf-8') as json_file:
        json.dump(reports_dict, json_file, ensure_ascii=False, indent=4)

    print("Reports have been written to 'recycling_reports.json'")
