# Imports for multiple parts
from viktor import ViktorController
from viktor.parametrization import ViktorParametrization, NumberField, Text
from io import StringIO
from pathlib import Path
# Imports for part 1
from viktor.geometry import CircularExtrusion, Group, Material, Color, Point, LinearPattern, Line
from viktor.views import GeometryView, GeometryResult
# Import for part 2
from viktor.parametrization import GeoPointField, GeoPolygonField
from viktor.views import MapPolygon, MapResult, MapPoint, MapView
# Import for part 3
import numpy as np 
import matplotlib.pyplot as plt
from viktor.views import ImageResult, ImageView
# Imports for part 4
from viktor.external.word import render_word_file, WordFileTag
from viktor.utils import convert_word_to_pdf
from viktor.views import PDFResult, PDFView
from viktor.parametrization import TextField, DateField

class Parametrization(ViktorParametrization):
    #Parameters part 1 - 3D Model
    text_building = Text('## Building dimensions')
    building_diameter = NumberField('Building diameter', min=10, default=20)
    building_floors = NumberField('Number of floors', min=3, default=10)

    #Parameters part 2 - Interactive map
    text_map = Text('## Map inputs')
    building_plot = GeoPolygonField('Draw a polygon on the map')
    map_point = GeoPointField('Add a point to the map')

    #Parameters part 3 - Graphing
    text_graph = Text('## Graph inputs')
    percentage_green_energy = NumberField('Percentage green energy', variant='slider', min=0, max=100, default=50)
    weight_sustainable_materials = NumberField('Weight of sustainable materials', variant='slider', min=0, max=100, default=70)

    #Parameters part 4 - Reporting
    text_report = Text('## Report inputs')
    user_name = TextField('Your name')
    project_date = DateField('Choose a project date')

class Controller(ViktorController):
    label = 'My Entity Type'
    parametrization = Parametrization

    @GeometryView("3D model", duration_guess=1)
    def get_geometry(self, params, **kwargs):
        #Materials:
        glass = Material("Glass", color=Color(150, 150, 255))
        facade = Material("Concrete", color=Color(200,200,200))

        floor_glass = CircularExtrusion(
            diameter=params.building_diameter,
            line=Line(Point(0,0,0), Point(0,0,2)),
            material=glass
        )
        floor_facade = CircularExtrusion(
            diameter=params.building_diameter+1,
            line=Line(Point(0,0,0), Point(0,0,1)),
            material=facade
        )
        floor_facade.translate((0, 0, 2))
        floor = Group([floor_glass, floor_facade])
        building = LinearPattern(floor, direction=[0, 0, 1], number_of_elements=params.building_floors, spacing=3)
        return GeometryResult(building)
    

    @MapView("Map", duration_guess=1)
    def generate_map(self, params, **kwargs):
        features = [
            MapPoint( 52.5200, 13.4050, title='Berlin, Germany'),
            MapPoint(47.6062, -122.3321, title='Seattle, USA'),
            MapPoint(53.3498, -6.2603, title='Dublin, Ireland'),
            MapPoint(43.6511, -79.3470, title='Toronto, Canada'),
            MapPoint(41.3851, 2.1734, title='Barcelona, Spain'),
            MapPoint(-34.6037, -58.3816, title='Buenos Aires, Argentina'),
            MapPoint(-33.9249, 18.4241, title='Cape Town, South Africa')
        ]
        if params.map_point:
            features.append(MapPoint.from_geo_point(params.map_point, color=Color.blue()))
        
        if params.building_plot:
            features.append(MapPolygon.from_geo_polygon(params.building_plot))
        return MapResult(features)
    

    @ImageView("Graph", duration_guess=1)
    def generate_graph(self, params, **kwargs):
        # Define the ranges for office and sustainability
        office = np.linspace(0, 100, 101)
        sustainability = np.linspace(0, 100, 101)
        x, y = np.meshgrid(office, sustainability)
        # Calculate revenue per square meter
        rev_per_sqm =  x + params.weight_sustainable_materials / 100 * y + 0.5*params.percentage_green_energy
        # Plot the surface
        fig = plt.figure()
        plt.imshow(rev_per_sqm, extent=[0, 100, 0, 100], origin='lower', cmap='RdBu', aspect='auto', vmin=40 ,vmax=240)
        plt.colorbar(label='Avg. revenue per m^2')
        # Set labels and title
        plt.xlabel('Percentage offices')
        plt.ylabel('Percentage sustainable materials')
        plt.title('Average rent per square meter')
        svg_data = StringIO()
        fig.savefig(svg_data, format='svg')
        return ImageResult(svg_data)


    @PDFView("Report", duration_guess=1)
    def generate_report(self, params, **kwargs):
        components = []
        data = {
            "user_name": params.user_name,
            "project_date": str(params.project_date),
        }
        # make tags
        for tag, value in data.items():
            components.append(WordFileTag(tag, value))
        # Get path to template and render word file
        template_path = Path(__file__).parent / "report_template.docx"
        with open(template_path, 'rb') as template:
            word_file = render_word_file(template, components)
            pdf_file = convert_word_to_pdf(word_file.open_binary())
        return PDFResult(file=pdf_file)