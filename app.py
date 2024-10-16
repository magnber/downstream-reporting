import pandas as pd
from dataclasses import dataclass
from typing import List, Dict
import json

@dataclass
class Material:
    code: str
    description: str

@dataclass
class Facility:
    id: str
    name: str
    location: str  # City, Country

@dataclass
class MaterialTransformation:
    facility_id: str
    input_material_code: str
    output_material_code: str
    yield_percentage: float
    material_recycling_rate: float
    energy_recycling_rate: float
    losses: float

@dataclass
class EmissionFactorProcessing:
    facility_id: str
    material_code: str
    emission_factor: float  # kg CO2e per tonne processed

@dataclass
class EstimatedDistribution:
    output_material_code: str
    destination_country: str
    percentage: float  # Percentage of total output

@dataclass
class TransportEmissionFactor:
    mode_of_transport: str
    emission_factor: float  # kg CO2e per tonne-km

@dataclass
class AverageTransportDistance:
    facility_id: str
    destination_country: str
    average_distance: float  # km
    mode_of_transport: str

@dataclass
class AvoidedEmissionBenchmark:
    material_code: str
    avoided_emission: float  # kg CO2e per tonne recycled

@dataclass
class GeographicRegion:
    country: str
    region: str

class NGMetallAPI:
    def __init__(self):
        # Initialize data tables (same as before)
        self.material_codes = pd.DataFrame([
            {'Material Code': 'M001', 'Material Description': 'Complex Iron'},
            {'Material Code': 'M002', 'Material Description': 'Processed Iron'},
            # Add other materials as needed
        ])

        self.facilities = pd.DataFrame([
            {'Facility ID': 'F001', 'Facility Name': 'Facility A', 'Location': 'Oslo, Norway'},
            # Add other facilities as needed
        ])

        self.material_transformations = pd.DataFrame([
            {'Facility ID': 'F001',
             'Input Material Code': 'M001',
             'Output Material Codes': ['M002'],
             'Yield Percentages': [0.95],
             'Material Recycling Rate': 87.1,
             'Energy Recycling Rate': 0.0,
             'Losses': 5.0},
            # Add other transformations as needed
        ])

        # Flatten the material_transformations DataFrame to handle multiple output materials
        transformations_expanded = []
        for _, row in self.material_transformations.iterrows():
            for output_code, yield_percentage in zip(row['Output Material Codes'], row['Yield Percentages']):
                transformations_expanded.append({
                    'Facility ID': row['Facility ID'],
                    'Input Material Code': row['Input Material Code'],
                    'Output Material Code': output_code,
                    'Yield Percentage': yield_percentage,
                    'Material Recycling Rate': row['Material Recycling Rate'],
                    'Energy Recycling Rate': row['Energy Recycling Rate'],
                    'Losses': row['Losses']
                })
        self.material_transformations = pd.DataFrame(transformations_expanded)

        self.emission_factors_processing = pd.DataFrame([
            {'Facility ID': 'F001', 'Material Code': 'M001', 'Emission Factor': 19.5},
            # Add other emission factors as needed
        ])

        self.estimated_distribution = pd.DataFrame([
            {'Output Material Code': 'M002', 'Destination Country': 'Norway', 'Percentage': 50.0},
            {'Output Material Code': 'M002', 'Destination Country': 'Sweden', 'Percentage': 20.0},
            {'Output Material Code': 'M002', 'Destination Country': 'Denmark', 'Percentage': 8.3},
            {'Output Material Code': 'M002', 'Destination Country': 'Germany', 'Percentage': 14.4},
            {'Output Material Code': 'M002', 'Destination Country': 'China', 'Percentage': 7.3},
            # Add other distributions as needed
        ])

        self.transport_emission_factors = pd.DataFrame([
            {'Mode of Transport': 'Truck', 'Emission Factor': 0.05},
            {'Mode of Transport': 'Rail', 'Emission Factor': 0.02},
            {'Mode of Transport': 'Ship', 'Emission Factor': 0.01},
            # Add other transport modes as needed
        ])

        self.average_transport_distances = pd.DataFrame([
            {'Facility ID': 'F001', 'Destination Country': 'Norway', 'Average Distance': 500, 'Mode of Transport': 'Truck'},
            {'Facility ID': 'F001', 'Destination Country': 'Sweden', 'Average Distance': 800, 'Mode of Transport': 'Truck'},
            {'Facility ID': 'F001', 'Destination Country': 'Denmark', 'Average Distance': 1000, 'Mode of Transport': 'Truck'},
            {'Facility ID': 'F001', 'Destination Country': 'Germany', 'Average Distance': 1500, 'Mode of Transport': 'Rail'},
            {'Facility ID': 'F001', 'Destination Country': 'China', 'Average Distance': 20000, 'Mode of Transport': 'Ship'},
            # Add other distances as needed
        ])

        self.avoided_emissions_benchmarks = pd.DataFrame([
            {'Material Code': 'M001', 'Avoided Emissions': 3056},
            # Add other benchmarks as needed
        ])

        self.geographic_regions = pd.DataFrame([
            {'Country': 'Norway', 'Region': 'Nordics'},
            {'Country': 'Sweden', 'Region': 'Nordics'},
            {'Country': 'Denmark', 'Region': 'Nordics'},
            {'Country': 'Germany', 'Region': 'EU'},
            {'Country': 'China', 'Region': 'Asia'},
            # Add other countries and regions as needed
        ])

    def process_invoices(self, invoices: pd.DataFrame) -> List[Dict]:
        # Merge invoices with material transformations
        invoices = invoices.merge(
            self.material_transformations,
            left_on=['Facility ID', 'Material Code'],
            right_on=['Facility ID', 'Input Material Code'],
            how='left'
        )

        # Calculate output volumes
        invoices['Output Volume'] = invoices['Volume'] * invoices['Yield Percentage']

        # Merge with estimated distribution
        invoices = invoices.merge(
            self.estimated_distribution,
            on='Output Material Code',
            how='left'
        )

        # Calculate destination volumes
        invoices['Destination Volume'] = invoices['Output Volume'] * invoices['Percentage'] / 100

        # Merge with emission factors for processing and rename the column
        invoices = invoices.merge(
            self.emission_factors_processing,
            left_on=['Facility ID', 'Material Code'],
            right_on=['Facility ID', 'Material Code'],
            how='left'
        )
        invoices.rename(columns={'Emission Factor': 'Emission Factor Processing'}, inplace=True)

        # Calculate processing emissions
        invoices['Processing Emissions'] = invoices['Volume'] * invoices['Emission Factor Processing']

        # Merge with average transport distances
        invoices = invoices.merge(
            self.average_transport_distances,
            on=['Facility ID', 'Destination Country'],
            how='left'
        )

        # Merge with transport emission factors and rename the column
        invoices = invoices.merge(
            self.transport_emission_factors,
            on='Mode of Transport',
            how='left'
        )
        invoices.rename(columns={'Emission Factor': 'Emission Factor Transport'}, inplace=True)

        # Calculate transport emissions using the correct emission factor
        invoices['Transport Emissions'] = invoices['Destination Volume'] * invoices['Average Distance'] * invoices['Emission Factor Transport']

        # Calculate avoided emissions
        invoices = invoices.merge(
            self.avoided_emissions_benchmarks,
            on='Material Code',
            how='left'
        )
        invoices['Avoided Emissions'] = invoices['Volume'] * (invoices['Material Recycling Rate'] / 100) * invoices['Avoided Emissions']

        # Prepare detailed report per invoice line
        group_columns = ['Invoice ID', 'Customer ID', 'Delivery Date', 'Facility ID',
                        'Material Code', 'Output Material Code', 'Volume', 'Output Volume',
                        'Processing Emissions', 'Avoided Emissions']

        invoices_grouped = invoices.groupby(group_columns + ['Destination Country']).agg({
            'Destination Volume': 'sum',
            'Transport Emissions': 'sum'
        }).reset_index()

        # Convert data types to standard Python types and compile the report
        detailed_report = []
        for _, row in invoices_grouped.iterrows():
            report_line = {
                'Invoice ID': str(row['Invoice ID']),
                'Customer ID': str(row['Customer ID']),
                'Delivery Date': str(row['Delivery Date']),
                'Facility ID': str(row['Facility ID']),
                'Input Material Code': str(row['Material Code']),
                'Output Material Code': str(row['Output Material Code']),
                'Volume Delivered': float(row['Volume']),
                'Output Volume': float(row['Output Volume']),
                'Processing Emissions (kg CO2e)': float(row['Processing Emissions']),
                'Avoided Emissions (kg CO2e)': float(row['Avoided Emissions']),
                'Destination Country': str(row['Destination Country']),
                'Destination Volume': float(row['Destination Volume']),
                'Transport Emissions (kg CO2e)': float(row['Transport Emissions'])
            }
            detailed_report.append(report_line)

        return detailed_report

# Example usage
if __name__ == '__main__':
    # Sample invoice data with multiple invoices
    invoice_data = pd.DataFrame([
        {'Invoice ID': 'INV001',
         'Customer ID': 'Supplier001',
         'Delivery Date': '2023-10-01',
         'Facility ID': 'F001',
         'Material Code': 'M001',
         'Volume': 6000},
        {'Invoice ID': 'INV002',
         'Customer ID': 'Supplier002',
         'Delivery Date': '2023-10-02',
         'Facility ID': 'F001',
         'Material Code': 'M001',
         'Volume': 4000},
        # Add other invoices as needed
    ])

    api = NGMetallAPI()
    detailed_report = api.process_invoices(invoice_data)
    print("Generated Detailed Report:")
    for line in detailed_report:
        print(line)

    # Write the detailed report to a JSON file
    with open('detailed_report.json', 'w') as json_file:
        json.dump(detailed_report, json_file, indent=4)
    print("Detailed report has been written to 'detailed_report.json'")
