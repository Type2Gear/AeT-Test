import os
from fitparse import FitFile
import gpxpy
import numpy as np
from typing import Tuple, List, Union
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import pandas as pd

class HeartRateAnalyzer:
    def __init__(self, file_path: str):
        """Initialize the analyzer with a fitness file path."""
        self.file_path = file_path
        self.file_type = os.path.splitext(file_path)[1].lower()
        self.data = None
        self.start_time = None
        self.paces = []  # Store pace data in minutes per kilometer
        
    def load_data(self) -> None:
        """Load and parse the fitness file based on its type."""
        if self.file_type == '.fit':
            self._load_fit()
        elif self.file_type == '.gpx':
            self._load_gpx()
        else:
            raise ValueError(f"Unsupported file type: {self.file_type}")
            
        if self.data is None or len(self.data) == 0:
            raise ValueError("No data found in the file.")
            
        # Store the start time
        self.start_time = self.data['timestamp'][0]
        
    def _load_fit(self) -> None:
        """Load and parse a .fit file."""
        fitfile = FitFile(self.file_path)
        
        # Get all records
        records = []
        for record in fitfile.get_messages("record"):
            data = {}
            for field in record:
                data[field.name] = field.value
            records.append(data)
            
        # Convert to DataFrame
        self.data = pd.DataFrame(records)
        
        # Convert timestamp to datetime
        if 'timestamp' in self.data.columns:
            self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
            
    def _load_gpx(self) -> None:
        """Load and parse a .gpx file."""
        with open(self.file_path, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)
            
        records = []
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    data = {
                        'timestamp': point.time,
                        'heart_rate': point.extensions.get('heart_rate', None),
                        'speed': point.speed if hasattr(point, 'speed') else None
                    }
                    records.append(data)
                    
        # Convert to DataFrame
        self.data = pd.DataFrame(records)
        
    def get_preview_data(self):
        """Get the full dataset for preview visualization."""
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
            
        # Convert timestamps to seconds from start
        timestamps = [(ts - self.start_time).total_seconds() for ts in self.data['timestamp']]
        
        return {
            'timestamps': timestamps,
            'heart_rate': self.data['heart_rate'].tolist(),
            'speed': [s * 3.6 if s else 0 for s in self.data['speed'].tolist()],  # Convert to km/h
            'total_time': timestamps[-1],
            'time_unit': 'seconds'
        }
        
    def get_section_data(self, start_time, end_time):
        """Get data for a specific time section."""
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
            
        # Convert time strings to datetime objects
        start_dt = self.start_time + pd.Timedelta(seconds=float(start_time))
        end_dt = self.start_time + pd.Timedelta(seconds=float(end_time))
        
        # Filter data for the section
        mask = (self.data['timestamp'] >= start_dt) & (self.data['timestamp'] <= end_dt)
        section_data = self.data[mask]
        
        if len(section_data) == 0:
            raise ValueError(f"No data found in the specified time range: {start_time} to {end_time}")
            
        return section_data
        
    def calculate_averages(self, section_data):
        """Calculate average heart rate and pace for a section."""
        # Calculate average heart rate
        avg_hr = section_data['heart_rate'].mean()
        
        # Calculate average pace (min/km)
        speeds = section_data['speed'].dropna()
        if len(speeds) > 0:
            avg_speed = speeds.mean()  # m/s
            avg_pace = 16.6667 / avg_speed if avg_speed > 0 else None  # min/km
        else:
            avg_pace = None
            
        return {
            'average_hr': avg_hr,
            'average_pace': avg_pace
        }
        
    def compare_sections(self, section1_range, section2_range):
        """Compare two sections of the workout."""
        # Get data for both sections
        section1_data = self.get_section_data(section1_range[0], section1_range[1])
        section2_data = self.get_section_data(section2_range[0], section2_range[1])
        
        # Calculate averages for both sections
        section1_avg = self.calculate_averages(section1_data)
        section2_avg = self.calculate_averages(section2_data)
        
        # Calculate differences
        hr_diff = section2_avg['average_hr'] - section1_avg['average_hr']
        hr_percent_diff = (hr_diff / section1_avg['average_hr']) * 100 if section1_avg['average_hr'] else None
        
        # Calculate pace-to-heart rate ratio if both metrics are available
        pace_hr_ratio = None
        if section1_avg['average_pace'] and section2_avg['average_pace']:
            phr1 = section1_avg['average_pace'] / section1_avg['average_hr']
            phr2 = section2_avg['average_pace'] / section2_avg['average_hr']
            phr_diff = ((phr2 - phr1) / phr1) * 100 if phr1 else None
            pace_hr_ratio = {
                'section1': phr1,
                'section2': phr2,
                'percent_difference': phr_diff
            }
        
        return {
            'section1': {
                'time_range': f"{section1_range[0]} to {section1_range[1]}",
                'average_hr': section1_avg['average_hr'],
                'average_pace': section1_avg['average_pace']
            },
            'section2': {
                'time_range': f"{section2_range[0]} to {section2_range[1]}",
                'average_hr': section2_avg['average_hr'],
                'average_pace': section2_avg['average_pace']
            },
            'heart_rate': {
                'difference': hr_diff,
                'percent_difference': hr_percent_diff
            },
            'pace_heart_rate_ratio': pace_hr_ratio
        }
        
    def plot_data(self, section1_range, section2_range, output_file=None):
        """Plot heart rate and pace data with highlighted sections."""
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
            
        # Create figure with two y-axes
        fig, ax1 = plt.subplots(figsize=(12, 6))
        ax2 = ax1.twinx()
        
        # Convert timestamps to seconds from start for x-axis
        timestamps = [(ts - self.start_time).total_seconds() for ts in self.data['timestamp']]
        
        # Plot heart rate
        ax1.plot(timestamps, self.data['heart_rate'], 'b-', label='Heart Rate')
        ax1.set_xlabel('Time (seconds)')
        ax1.set_ylabel('Heart Rate (BPM)', color='b')
        ax1.tick_params(axis='y', labelcolor='b')
        
        # Plot speed (converted to km/h)
        speeds = [s * 3.6 if s else 0 for s in self.data['speed']]  # Convert m/s to km/h
        ax2.plot(timestamps, speeds, 'r-', label='Speed')
        ax2.set_ylabel('Speed (km/h)', color='r')
        ax2.tick_params(axis='y', labelcolor='r')
        
        # Highlight sections
        for start, end, color in [(section1_range[0], section1_range[1], 'lightblue'),
                                (section2_range[0], section2_range[1], 'lightgreen')]:
            ax1.axvspan(float(start), float(end), alpha=0.2, color=color)
            
        # Add legend
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        plt.title('Heart Rate and Speed Analysis')
        
        if output_file:
            plt.savefig(output_file)
            plt.close()
        else:
            plt.show()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze heart rate data from fitness files')
    parser.add_argument('file_path', help='Path to the .fit or .gpx file')
    parser.add_argument('--section1-start', required=True, help='Start time for section 1 (HH:MM:SS)')
    parser.add_argument('--section1-end', required=True, help='End time for section 1 (HH:MM:SS)')
    parser.add_argument('--section2-start', required=True, help='Start time for section 2 (HH:MM:SS)')
    parser.add_argument('--section2-end', required=True, help='End time for section 2 (HH:MM:SS)')
    parser.add_argument('--plot', action='store_true', help='Generate plots of the data')
    parser.add_argument('--plot-file', help='Save plot to specified file')
    
    args = parser.parse_args()
    
    analyzer = HeartRateAnalyzer(args.file_path)
    analyzer.load_data()
    
    result = analyzer.compare_sections(
        (args.section1_start, args.section1_end),
        (args.section2_start, args.section2_end)
    )
    
    print("\nHeart Rate Analysis Results:")
    print(f"Section 1 ({result['section1']['time_range']}):")
    print(f"  Average Heart Rate: {result['section1']['average_hr']:.1f} BPM")
    if result['section1']['average_pace'] is not None:
        print(f"  Average Pace: {result['section1']['average_pace']:.2f} min/km")
    
    print(f"\nSection 2 ({result['section2']['time_range']}):")
    print(f"  Average Heart Rate: {result['section2']['average_hr']:.1f} BPM")
    if result['section2']['average_pace'] is not None:
        print(f"  Average Pace: {result['section2']['average_pace']:.2f} min/km")
    
    print(f"\nOverall Averages:")
    print(f"  Average Heart Rate: {result['overall']['average_hr']:.1f} BPM")
    if result['overall']['average_pace'] is not None:
        print(f"  Average Pace: {result['overall']['average_pace']:.2f} min/km")
    
    print(f"\nHeart Rate Differences:")
    print(f"  Absolute Difference: {result['heart_rate']['difference']:.1f} BPM")
    print(f"  Percentage Difference: {result['heart_rate']['percent_difference']:.1f}%")
    
    if 'pace_heart_rate_ratio' in result:
        print(f"\nPace-to-Heart Rate Ratio:")
        print(f"  Section 1: {result['pace_heart_rate_ratio']['section1']:.4f} min/km/BPM")
        print(f"  Section 2: {result['pace_heart_rate_ratio']['section2']:.4f} min/km/BPM")
        print(f"  Percentage Difference: {result['pace_heart_rate_ratio']['percent_difference']:.1f}%")
    
    if args.plot:
        analyzer.plot_data(
            (args.section1_start, args.section1_end),
            (args.section2_start, args.section2_end),
            args.plot_file
        )

if __name__ == '__main__':
    main() 