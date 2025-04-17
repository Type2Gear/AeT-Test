import unittest
from datetime import datetime
from src.heart_rate_analyzer import HeartRateAnalyzer

class TestHeartRateAnalyzer(unittest.TestCase):
    def setUp(self):
        # Create a test instance
        self.analyzer = HeartRateAnalyzer("test.fit")
        
    def test_parse_time(self):
        """Test time string parsing"""
        time_str = "10:30:00"
        parsed_time = self.analyzer._parse_time(time_str)
        self.assertIsInstance(parsed_time, datetime)
        self.assertEqual(parsed_time.hour, 10)
        self.assertEqual(parsed_time.minute, 30)
        self.assertEqual(parsed_time.second, 0)
        
    def test_invalid_file_type(self):
        """Test handling of invalid file types"""
        analyzer = HeartRateAnalyzer("test.txt")
        with self.assertRaises(ValueError):
            analyzer.load_data()
            
    def test_invalid_time_format(self):
        """Test handling of invalid time formats"""
        with self.assertRaises(ValueError):
            self.analyzer._parse_time("10:30")  # Missing seconds
            
    def test_section_validation(self):
        """Test section time validation"""
        with self.assertRaises(ValueError):
            self.analyzer.calculate_section_average("00:15:00", "00:10:00")  # End before start

if __name__ == '__main__':
    unittest.main() 