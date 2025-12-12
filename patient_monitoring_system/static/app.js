// Patient Monitoring System - Frontend JavaScript

const socket = io();
let uploadedVideoPath = null;

// DOM Elements
const videoFrame = document.getElementById('videoFrame');
const videoPlaceholder = document.getElementById('videoPlaceholder');
const videoSource = document.getElementById('videoSource');
const videoFile = document.getElementById('videoFile');
const fileUploadGroup = document.getElementById('fileUploadGroup');
const uploadBtn = document.getElementById('uploadBtn');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const statusIndicator = document.getElementById('statusIndicator');
const statusText = document.getElementById('statusText');
const fpsValue = document.getElementById('fpsValue');
const heartRate = document.getElementById('heartRate');
const respRate = document.getElementById('respRate');
const signalQuality = document.getElementById('signalQuality');
const alertsList = document.getElementById('alertsList');
const eventsList = document.getElementById('eventsList');

// Event Listeners
videoSource.addEventListener('change', handleSourceChange);
uploadBtn.addEventListener('click', handleUpload);
startBtn.addEventListener('click', startMonitoring);
stopBtn.addEventListener('click', stopMonitoring);

// Socket.IO Event Handlers
socket.on('connect', () => {
    console.log('✅ Socket.IO Connected to server');
    console.log('Socket ID:', socket.id);
});

socket.on('disconnect', (reason) => {
    console.log('❌ Socket.IO Disconnected:', reason);
});

socket.on('connect_error', (error) => {
    console.error('❌ Socket.IO Connection Error:', error);
});

socket.on('frame_update', (data) => {
    console.log('📹 Frame received:', data.frame.substring(0, 20) + '...', 'FPS:', data.fps);
    // Update video frame
    videoFrame.src = 'data:image/jpeg;base64,' + data.frame;
    videoFrame.classList.add('active');
    videoPlaceholder.style.display = 'none';

    // Update FPS
    fpsValue.textContent = data.fps.toFixed(1);

    // Update events
    updateEvents(data.events);

    // Update alerts
    updateAlerts(data.alerts);
});

socket.on('monitoring_stopped', (data) => {
    console.log('⏹️ Monitoring stopped:', data.reason);
    handleMonitoringStopped();
    alert('Monitoring stopped: ' + data.reason);
});

// Functions
function handleSourceChange() {
    if (videoSource.value === 'uploaded') {
        fileUploadGroup.style.display = 'block';
    } else {
        fileUploadGroup.style.display = 'none';
    }
}

async function handleUpload() {
    const file = videoFile.files[0];
    if (!file) {
        alert('Please select a video file');
        return;
    }

    const formData = new FormData();
    formData.append('video', file);

    uploadBtn.disabled = true;
    uploadBtn.textContent = 'Uploading...';

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            uploadedVideoPath = data.path;
            alert('Video uploaded successfully!');
            uploadBtn.textContent = '✓ Uploaded';
        } else {
            alert('Upload failed: ' + data.error);
            uploadBtn.textContent = 'Upload';
            uploadBtn.disabled = false;
        }
    } catch (error) {
        alert('Upload error: ' + error.message);
        uploadBtn.textContent = 'Upload';
        uploadBtn.disabled = false;
    }
}

async function startMonitoring() {
    let source = videoSource.value;

    if (source === 'uploaded') {
        if (!uploadedVideoPath) {
            alert('Please upload a video first');
            return;
        }
        source = uploadedVideoPath;
    }

    startBtn.disabled = true;
    startBtn.textContent = 'Starting...';

    try {
        const response = await fetch('/api/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ source: source })
        });

        const data = await response.json();

        if (response.ok) {
            handleMonitoringStarted();
        } else {
            alert('Failed to start: ' + data.error);
            startBtn.disabled = false;
            startBtn.textContent = '▶ Start Monitoring';
        }
    } catch (error) {
        alert('Error: ' + error.message);
        startBtn.disabled = false;
        startBtn.textContent = '▶ Start Monitoring';
    }
}

async function stopMonitoring() {
    stopBtn.disabled = true;

    try {
        const response = await fetch('/api/stop', {
            method: 'POST'
        });

        if (response.ok) {
            handleMonitoringStopped();
        }
    } catch (error) {
        alert('Error: ' + error.message);
        stopBtn.disabled = false;
    }
}

function handleMonitoringStarted() {
    statusIndicator.classList.add('active');
    statusText.textContent = 'Active';
    startBtn.disabled = true;
    stopBtn.disabled = false;
    videoSource.disabled = true;
}

function handleMonitoringStopped() {
    statusIndicator.classList.remove('active');
    statusText.textContent = 'Inactive';
    startBtn.disabled = false;
    startBtn.textContent = '▶ Start Monitoring';
    stopBtn.disabled = true;
    videoSource.disabled = false;

    // Reset displays
    videoFrame.classList.remove('active');
    videoPlaceholder.style.display = 'block';
    fpsValue.textContent = '0';
}

function updateEvents(events) {
    if (events.length === 0) {
        eventsList.innerHTML = '<p class="no-data">No events</p>';
        return;
    }

    // Keep last 10 events
    const recentEvents = events.slice(-10).reverse();

    eventsList.innerHTML = recentEvents.map(event => {
        const time = new Date(event.timestamp * 1000).toLocaleTimeString();
        const confidence = (event.confidence * 100).toFixed(0);

        return `
            <div class="event-item">
                <div class="event-type">${formatEventType(event.type)}</div>
                <div class="event-confidence">Confidence: ${confidence}% | ${time}</div>
            </div>
        `;
    }).join('');

    // Update vital signs if present
    events.forEach(event => {
        if (event.type === 'vital_signs') {
            // Vital signs are updated separately in the frame_update handler
        }
    });
}

function updateAlerts(alerts) {
    if (alerts.length === 0) {
        alertsList.innerHTML = '<p class="no-data">No alerts</p>';
        return;
    }

    alertsList.innerHTML = alerts.map(alert => {
        const time = new Date(alert.timestamp * 1000).toLocaleTimeString();

        return `
            <div class="alert-item alert-${alert.level}">
                <div>
                    <span class="alert-level">[${alert.level}]</span>
                    <span class="alert-message">${alert.message}</span>
                </div>
                <div class="alert-time">${time}</div>
            </div>
        `;
    }).join('');
}

function formatEventType(type) {
    return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

// Check status on load
async function checkStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        if (data.active) {
            handleMonitoringStarted();
        }
    } catch (error) {
        console.error('Failed to check status:', error);
    }
}

checkStatus();
