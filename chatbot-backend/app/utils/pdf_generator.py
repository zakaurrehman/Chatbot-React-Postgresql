# app/utils/pdf_generator.py
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing
import matplotlib.pyplot as plt
import io
from datetime import datetime

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
    
    def generate_project_report(self, project_data):
        """Generate a PDF report for a project."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        
        # Add title
        title = Paragraph(f"Project Report: {project_data['name']}", self.styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Add generated date
        date_text = Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", self.styles['Normal'])
        story.append(date_text)
        story.append(Spacer(1, 12))
        
        # Add project details
        project_details = Paragraph("Project Details", self.styles['Heading2'])
        story.append(project_details)
        story.append(Spacer(1, 6))
        
        # Format the start date nicely if it's a date object
        start_date = project_data.get('startDate', 'Unknown')
        if hasattr(start_date, 'strftime'):
            start_date = start_date.strftime('%m/%d/%Y')
        
        details = [
            [Paragraph("Project Name:", self.styles['Bold']), project_data['name']],
            [Paragraph("Start Date:", self.styles['Bold']), start_date],
            [Paragraph("Designer:", self.styles['Bold']), project_data.get('designer_name', 'Not assigned')],
            [Paragraph("Developer:", self.styles['Bold']), project_data.get('developer_name', 'Not assigned')]
        ]
        
        # Add client info if available
        client_name = project_data.get('client_name')
        if client_name:
            details.append([Paragraph("Client:", self.styles['Bold']), client_name])
        
        # Add table with project details
        table = Table(details)
        story.append(table)
        story.append(Spacer(1, 12))
        
        # Add phase information
        phase_info = project_data.get('phase_info', {})
        phases = phase_info.get('phases', [])
        
        if phases:
            phase_heading = Paragraph("Project Phases", self.styles['Heading2'])
            story.append(phase_heading)
            story.append(Spacer(1, 6))
            
            phase_data = [["Phase", "Status", "Progress"]]
            for phase in phases:
                phase_data.append([
                    phase.get('name', 'Unknown'),
                    phase.get('status', 'Unknown'),
                    f"{phase.get('progress', 0):.1f}%"
                ])
            
            phase_table = Table(phase_data)
            story.append(phase_table)
            story.append(Spacer(1, 12))
            
            # Add phase progress chart
            chart_heading = Paragraph("Phase Progress Chart", self.styles['Heading2'])
            story.append(chart_heading)
            story.append(Spacer(1, 6))
            
            # Create matplotlib figure
            plt.figure(figsize=(7, 3.5))
            
            # Extract data
            phase_names = [phase.get('name', 'Unknown').replace('Phase ', 'P') for phase in phases]
            phase_progress = [phase.get('progress', 0) for phase in phases]
            
            # Create the bar chart
            plt.bar(phase_names, phase_progress)
            plt.title('Phase Progress')
            plt.xlabel('Phases')
            plt.ylabel('Progress (%)')
            plt.ylim(0, 100)  # Set y-axis from 0 to 100%
            plt.tight_layout()
            
            # Save the chart to a buffer
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png')
            img_buffer.seek(0)
            
            # Add the image to the story
            img = Image(img_buffer, width=400, height=200)
            story.append(img)
            plt.close()
            story.append(Spacer(1, 12))
        
        # Add current phase details
        current_phase = phase_info.get('current_phase')
        if current_phase:
            current_phase_heading = Paragraph("Current Phase Details", self.styles['Heading2'])
            story.append(current_phase_heading)
            story.append(Spacer(1, 6))
            
            current_phase_text = Paragraph(f"Current Phase: {current_phase.get('name', 'Unknown')}", self.styles['Normal'])
            story.append(current_phase_text)
            story.append(Spacer(1, 6))
            
            # Add subphases if available
            if 'subphases' in current_phase:
                subphases = current_phase['subphases']
                
                subphase_heading = Paragraph("Tasks in Current Phase", self.styles['Heading3'])
                story.append(subphase_heading)
                story.append(Spacer(1, 6))
                
                task_data = [["Task", "Status"]]
                for subphase in subphases:
                    if hasattr(subphase, 'get'):
                        task_data.append([
                            subphase.get('name', 'Unknown'),
                            subphase.get('status', 'Unknown')
                        ])
                    elif isinstance(subphase, dict):
                        task_data.append([
                            subphase.get('name', 'Unknown'),
                            subphase.get('status', 'Unknown')
                        ])
                
                task_table = Table(task_data)
                story.append(task_table)
        
        # Build the PDF
        doc.build(story)
        
        # Get the PDF content
        pdf = buffer.getvalue()
        buffer.close()
        
        return pdf
    
    def generate_project_comparison_report(self, projects_data):
        """Generate a PDF report comparing multiple projects."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        
        # Add title
        title = Paragraph("Projects Comparison Report", self.styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Add generated date
        date_text = Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", self.styles['Normal'])
        story.append(date_text)
        story.append(Spacer(1, 12))
        
        # Add project comparison table
        comparison_heading = Paragraph("Project Progress Comparison", self.styles['Heading2'])
        story.append(comparison_heading)
        story.append(Spacer(1, 6))
        
        # Create comparison table
        comparison_data = [["Project", "Current Phase", "Progress"]]
        project_names = []
        project_progress = []
        
        for project in projects_data:
            # Get current phase
            phase_info = project.get('phase_info', {})
            current_phase = phase_info.get('current_phase', {})
            current_phase_name = current_phase.get('name', 'Unknown') if current_phase else 'Unknown'
            overall_progress = phase_info.get('overall_progress', 0)
            
            # Add to table data
            comparison_data.append([
                project['name'],
                current_phase_name,
                f"{overall_progress:.1f}%"
            ])
            
            # Collect data for chart
            project_names.append(project['name'])
            project_progress.append(overall_progress)
        
        comparison_table = Table(comparison_data)
        story.append(comparison_table)
        story.append(Spacer(1, 12))
        
        # Add comparison chart
        chart_heading = Paragraph("Progress Comparison Chart", self.styles['Heading2'])
        story.append(chart_heading)
        story.append(Spacer(1, 6))
        
        # Create matplotlib figure
        plt.figure(figsize=(7, 4))
        
        # Create the bar chart
        plt.bar(project_names, project_progress)
        plt.title('Project Progress Comparison')
        plt.xlabel('Projects')
        plt.ylabel('Progress (%)')
        plt.ylim(0, 100)  # Set y-axis from 0 to 100%
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Save the chart to a buffer
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        
        # Add the image to the story
        img = Image(img_buffer, width=400, height=250)
        story.append(img)
        plt.close()
        
        # Build the PDF
        doc.build(story)
        
        # Get the PDF content
        pdf = buffer.getvalue()
        buffer.close()
        
        return pdf