import streamlit as st
import pandas as pd
import sqlite3
import altair as alt

def main():
    st.title("NG Metall Environmental Impact Dashboard")

    # Connect to the SQLite database
    conn = sqlite3.connect('ngmetall.db')

    # Read data from the database
    df = pd.read_sql_query("""
        SELECT 
            category, 
            output_volume, 
            output_material_code, 
            processing_emissions, 
            inbound_transport_emissions,
            outbound_transport_emissions,
            total_transport_emissions,
            avoided_emissions
        FROM output_data
    """, conn)

    # Check if the DataFrame is empty
    if df.empty:
        st.warning("No data available in the database.")
    else:
        # First Chart: Tonnage per Category
        st.header("Tonnage per Category")

        # Aggregate tonnage per category
        tonnage_per_category = df.groupby('category')['output_volume'].sum().reset_index()
        tonnage_per_category.columns = ['Category', 'Total Tonnage']

        # Display the data in a table
        st.subheader("Aggregated Tonnage Data")
        st.dataframe(tonnage_per_category)

        # Create a bar chart using Altair
        chart1 = alt.Chart(tonnage_per_category).mark_bar().encode(
            x=alt.X('Category', sort=['Material Recycling', 'Energy Recycling', 'Losses']),
            y='Total Tonnage',
            tooltip=['Category', 'Total Tonnage']
        ).properties(
            title='Tonnage per Category'
        )

        # Display the chart
        st.altair_chart(chart1, use_container_width=True)

        # Second Chart: Emissions vs. Avoided Emissions per Output Material Code
        st.header("Emissions and Avoided Emissions per Output Material")

        # Exclude 'Losses' and 'Energy Recovery' from the DataFrame
        df_materials = df[~df['output_material_code'].isin(['Losses', 'Energy Recovery'])]

        # Check if there are any relevant materials
        if df_materials.empty:
            st.warning("No data available for actual output materials.")
        else:
            # Calculate total emissions per output material code
            df_materials['Total Emissions'] = (
                df_materials['processing_emissions'] + df_materials['total_transport_emissions']
            )

            emissions_per_material = df_materials.groupby('output_material_code').agg({
                'Total Emissions': 'sum',
                'avoided_emissions': 'sum'
            }).reset_index()

            emissions_per_material.columns = ['Output Material Code', 'Total Emissions (kg CO2e)', 'Avoided Emissions (kg CO2e)']

            # Melt the DataFrame for plotting
            emissions_melted = emissions_per_material.melt(
                id_vars=['Output Material Code'],
                value_vars=['Total Emissions (kg CO2e)', 'Avoided Emissions (kg CO2e)'],
                var_name='Emission Type',
                value_name='Emissions (kg CO2e)'
            )

            # Display the data in a table
            st.subheader("Emissions Data per Output Material")
            st.dataframe(emissions_per_material)

            # Create a bar chart to compare emissions and avoided emissions
            chart2 = alt.Chart(emissions_melted).mark_bar().encode(
                x=alt.X('Output Material Code:N'),
                y=alt.Y('Emissions (kg CO2e):Q'),
                color='Emission Type',
                tooltip=['Output Material Code', 'Emission Type', 'Emissions (kg CO2e)']
            ).properties(
                title='Total Emissions vs. Avoided Emissions per Output Material'
            )

            # Display the chart
            st.altair_chart(chart2, use_container_width=True)
    
    # Close the database connection
    conn.close()

if __name__ == '__main__':
    main()
