class HeartRateAnalyzer {
    constructor() {
        this.data = [];
        this.startTime = null;
        this.fileType = null;
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        const uploadButton = document.getElementById('uploadButton');
        const fileInput = document.getElementById('fileInput');
        const analyzeButton = document.getElementById('analyzeButton');
        const startRange = document.getElementById('startRange');
        const endRange = document.getElementById('endRange');

        uploadButton.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
        analyzeButton.addEventListener('click', () => this.analyzeSections());
        startRange.addEventListener('input', (e) => this.updateTimeDisplay(e, 'startTime'));
        endRange.addEventListener('input', (e) => this.updateTimeDisplay(e, 'endTime'));
    }

    async handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        try {
            await this.loadFile(file);
            this.showPreviewSection();
            this.updateCharts();
        } catch (error) {
            console.error('Error loading file:', error);
            alert('Error loading file. Please try again.');
        }
    }

    async loadFile(file) {
        const fileType = file.name.split('.').pop().toLowerCase();
        
        if (fileType === 'fit') {
            await this._loadFIT(file);
        } else if (fileType === 'gpx') {
            await this._loadGPX(file);
        } else {
            throw new Error('Unsupported file type');
        }

        if (!this.data || this.data.length === 0) {
            throw new Error('No data found in the file.');
        }

        this.startTime = new Date(this.data[0].timestamp);
    }

    async _loadGPX(file) {
        const text = await file.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(text, 'text/xml');
        const tracks = doc.getElementsByTagName('trk');
        
        this.data = [];
        for (const track of tracks) {
            const segments = track.getElementsByTagName('trkseg');
            for (const segment of segments) {
                const points = segment.getElementsByTagName('trkpt');
                for (const point of points) {
                    const time = point.getElementsByTagName('time')[0]?.textContent;
                    const extensions = point.getElementsByTagName('extensions')[0];
                    const heartRate = extensions?.querySelector('gpxtpx\\:hr, hr')?.textContent;
                    const speed = point.getAttribute('speed');
                    
                    if (time) {
                        this.data.push({
                            timestamp: new Date(time).getTime(),
                            heart_rate: heartRate ? parseInt(heartRate) : null,
                            speed: speed ? parseFloat(speed) : null
                        });
                    }
                }
            }
        }
    }

    async _loadFIT(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = async (e) => {
                try {
                    const buffer = e.target.result;
                    const parser = new FitParser();
                    
                    parser.on('data', (data) => {
                        if (data.record && data.record.heart_rate && data.record.timestamp) {
                            this.data.push({
                                timestamp: new Date(data.record.timestamp).getTime(),
                                heartRate: data.record.heart_rate,
                                speed: data.record.speed ? data.record.speed * 3.6 : null // Convert m/s to km/h
                            });
                        }
                    });

                    parser.on('end', () => {
                        this.data.sort((a, b) => a.timestamp - b.timestamp);
                        resolve();
                    });

                    parser.parse(buffer);
                } catch (error) {
                    reject(error);
                }
            };
            reader.onerror = () => reject(new Error('Error reading file'));
            reader.readAsArrayBuffer(file);
        });
    }

    getPreviewData() {
        if (!this.data) {
            throw new Error('No data loaded. Call loadFile() first.');
        }

        const timestamps = this.data.map(d => 
            (d.timestamp - this.startTime) / 1000
        );

        return {
            timestamps: timestamps,
            heart_rate: this.data.map(d => d.heart_rate),
            speed: this.data.map(d => d.speed ? d.speed * 3.6 : 0), // Convert to km/h
            total_time: timestamps[timestamps.length - 1],
            time_unit: 'seconds'
        };
    }

    getSectionData(startTime, endTime) {
        if (!this.data) {
            throw new Error('No data loaded. Call loadFile() first.');
        }

        const startDt = new Date(this.startTime.getTime() + startTime * 1000);
        const endDt = new Date(this.startTime.getTime() + endTime * 1000);

        return this.data.filter(d => 
            d.timestamp >= startDt && d.timestamp <= endDt
        );
    }

    calculateAverages(sectionData) {
        const heartRates = sectionData.map(d => d.heart_rate).filter(h => h !== null);
        const speeds = sectionData.map(d => d.speed).filter(s => s !== null);

        const avgHr = heartRates.length > 0 ? 
            heartRates.reduce((a, b) => a + b) / heartRates.length : null;

        const avgSpeed = speeds.length > 0 ? 
            speeds.reduce((a, b) => a + b) / speeds.length : null;

        const avgPace = avgSpeed ? 16.6667 / avgSpeed : null; // min/km

        return {
            average_hr: avgHr,
            average_pace: avgPace
        };
    }

    compareSections(section1Range, section2Range) {
        const section1Data = this.getSectionData(section1Range[0], section1Range[1]);
        const section2Data = this.getSectionData(section2Range[0], section2Range[1]);

        if (section1Data.length === 0 || section2Data.length === 0) {
            throw new Error('No data found in one or both sections');
        }

        const section1Avg = this.calculateAverages(section1Data);
        const section2Avg = this.calculateAverages(section2Data);

        const hrDiff = section2Avg.average_hr - section1Avg.average_hr;
        const hrPercentDiff = section1Avg.average_hr ? 
            (hrDiff / section1Avg.average_hr) * 100 : null;

        let paceHrRatio = null;
        if (section1Avg.average_pace && section2Avg.average_pace) {
            const phr1 = section1Avg.average_pace / section1Avg.average_hr;
            const phr2 = section2Avg.average_pace / section2Avg.average_hr;
            const phrDiff = phr1 ? ((phr2 - phr1) / phr1) * 100 : null;
            paceHrRatio = {
                section1: phr1,
                section2: phr2,
                percent_difference: phrDiff
            };
        }

        return {
            section1: {
                time_range: `${section1Range[0]} to ${section1Range[1]}`,
                average_hr: section1Avg.average_hr,
                average_pace: section1Avg.average_pace
            },
            section2: {
                time_range: `${section2Range[0]} to ${section2Range[1]}`,
                average_hr: section2Avg.average_hr,
                average_pace: section2Avg.average_pace
            },
            heart_rate: {
                difference: hrDiff,
                percent_difference: hrPercentDiff
            },
            pace_heart_rate_ratio: paceHrRatio
        };
    }

    showPreviewSection() {
        const previewSection = document.getElementById('previewSection');
        previewSection.style.display = 'block';
    }

    updateCharts() {
        const previewData = this.getPreviewData();
        this.updatePreviewChart(previewData);
    }

    updatePreviewChart(data) {
        const ctx = document.getElementById('previewChart').getContext('2d');
        if (previewChart) {
            previewChart.destroy();
        }

        previewChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.timestamps,
                datasets: [
                    {
                        label: 'Heart Rate (BPM)',
                        data: data.heart_rate,
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Speed (km/h)',
                        data: data.speed,
                        borderColor: 'rgb(255, 99, 132)',
                        tension: 0.1,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Heart Rate (BPM)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Speed (km/h)'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
    }

    updateTimeDisplay(event, elementId) {
        const value = event.target.value;
        const element = document.getElementById(elementId);
        element.textContent = this.formatTime(value);
    }

    formatTime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    analyzeSections() {
        if (!this.data) {
            alert('Please upload a file first');
            return;
        }

        try {
            const result = this.compareSections(
                [parseFloat(startRange.value), parseFloat(endRange.value)],
                [parseFloat(endRange.value), parseFloat(endRange.value) + 300] // 5 minutes after end
            );
            this.updateResults(result);
            const resultsSection = document.getElementById('resultsSection');
            resultsSection.style.display = 'block';
        } catch (error) {
            alert(error.message);
        }
    }

    updateResults(result) {
        // Update the results table
        document.getElementById('section1Hr').textContent = 
            result.section1.average_hr ? result.section1.average_hr.toFixed(1) : 'N/A';
        document.getElementById('section1Pace').textContent = 
            result.section1.average_pace ? result.section1.average_pace.toFixed(2) : 'N/A';
        document.getElementById('section2Hr').textContent = 
            result.section2.average_hr ? result.section2.average_hr.toFixed(1) : 'N/A';
        document.getElementById('section2Pace').textContent = 
            result.section2.average_pace ? result.section2.average_pace.toFixed(2) : 'N/A';
        document.getElementById('hrDiff').textContent = 
            result.heart_rate.difference ? result.heart_rate.difference.toFixed(1) : 'N/A';
        document.getElementById('hrPercentDiff').textContent = 
            result.heart_rate.percent_difference ? result.heart_rate.percent_difference.toFixed(1) : 'N/A';

        // Update the pace-to-heart rate ratio if available
        const phrSection = document.getElementById('phrSection');
        if (result.pace_heart_rate_ratio) {
            phrSection.style.display = 'block';
            document.getElementById('phr1').textContent = 
                result.pace_heart_rate_ratio.section1.toFixed(3);
            document.getElementById('phr2').textContent = 
                result.pace_heart_rate_ratio.section2.toFixed(3);
            document.getElementById('phrDiff').textContent = 
                result.pace_heart_rate_ratio.percent_difference.toFixed(1);
        } else {
            phrSection.style.display = 'none';
        }
    }
}

// Initialize the analyzer and set up event listeners
document.addEventListener('DOMContentLoaded', () => {
    const analyzer = new HeartRateAnalyzer();
    let previewChart = null;
    let resultsChart = null;

    // File upload handling
    const fileInput = document.getElementById('fileInput');
    const uploadButton = document.getElementById('uploadButton');
    const previewSection = document.getElementById('previewSection');
    const resultsSection = document.getElementById('resultsSection');

    uploadButton.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', async (e) => {
        if (e.target.files.length === 0) return;

        try {
            await analyzer.loadFile(e.target.files[0]);
            const previewData = analyzer.getPreviewData();
            updatePreviewChart(previewData);
            previewSection.style.display = 'block';
            resultsSection.style.display = 'none';
        } catch (error) {
            alert(error.message);
        }
    });

    // Range slider handling
    const startRange = document.getElementById('startRange');
    const endRange = document.getElementById('endRange');
    const startTime = document.getElementById('startTime');
    const endTime = document.getElementById('endTime');
    const analyzeButton = document.getElementById('analyzeButton');

    function updateTimeDisplay() {
        const start = formatTime(startRange.value);
        const end = formatTime(endRange.value);
        startTime.textContent = start;
        endTime.textContent = end;
    }

    function formatTime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    startRange.addEventListener('input', updateTimeDisplay);
    endRange.addEventListener('input', updateTimeDisplay);

    analyzeButton.addEventListener('click', () => {
        if (!analyzer.data) {
            alert('Please upload a file first');
            return;
        }

        try {
            const result = analyzer.compareSections(
                [parseFloat(startRange.value), parseFloat(endRange.value)],
                [parseFloat(endRange.value), parseFloat(endRange.value) + 300] // 5 minutes after end
            );
            updateResults(result);
            resultsSection.style.display = 'block';
        } catch (error) {
            alert(error.message);
        }
    });

    function updatePreviewChart(data) {
        if (previewChart) {
            previewChart.destroy();
        }

        const ctx = document.getElementById('previewChart').getContext('2d');
        previewChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.timestamps,
                datasets: [
                    {
                        label: 'Heart Rate (BPM)',
                        data: data.heart_rate,
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Speed (km/h)',
                        data: data.speed,
                        borderColor: 'rgb(255, 99, 132)',
                        tension: 0.1,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Heart Rate (BPM)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Speed (km/h)'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
    }

    function updateResults(result) {
        // Update the results table
        document.getElementById('section1Hr').textContent = 
            result.section1.average_hr ? result.section1.average_hr.toFixed(1) : 'N/A';
        document.getElementById('section1Pace').textContent = 
            result.section1.average_pace ? result.section1.average_pace.toFixed(2) : 'N/A';
        document.getElementById('section2Hr').textContent = 
            result.section2.average_hr ? result.section2.average_hr.toFixed(1) : 'N/A';
        document.getElementById('section2Pace').textContent = 
            result.section2.average_pace ? result.section2.average_pace.toFixed(2) : 'N/A';
        document.getElementById('hrDiff').textContent = 
            result.heart_rate.difference ? result.heart_rate.difference.toFixed(1) : 'N/A';
        document.getElementById('hrPercentDiff').textContent = 
            result.heart_rate.percent_difference ? result.heart_rate.percent_difference.toFixed(1) : 'N/A';

        // Update the pace-to-heart rate ratio if available
        const phrSection = document.getElementById('phrSection');
        if (result.pace_heart_rate_ratio) {
            phrSection.style.display = 'block';
            document.getElementById('phr1').textContent = 
                result.pace_heart_rate_ratio.section1.toFixed(3);
            document.getElementById('phr2').textContent = 
                result.pace_heart_rate_ratio.section2.toFixed(3);
            document.getElementById('phrDiff').textContent = 
                result.pace_heart_rate_ratio.percent_difference.toFixed(1);
        } else {
            phrSection.style.display = 'none';
        }
    }
}); 