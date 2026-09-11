// =============================================
// CROWD SAFETY MONITOR
// PHASE 2B
// YOLO PERSON DETECTION
// =============================================


// =============================================
// HTML ELEMENTS
// =============================================

const cameraFeed =
    document.getElementById("cameraFeed");

const cameraError =
    document.getElementById("cameraError");

const connectionText =
    document.getElementById("connectionText");

const streamStatus =
    document.getElementById("streamStatus");

const streamIndicator =
    document.getElementById("streamIndicator");

const peopleCount =
    document.getElementById("peopleCount");

const crowdStatus =
    document.getElementById("crowdStatus");

const crowdMessage =
    document.getElementById("crowdMessage");

const eventLog =
    document.getElementById("eventLog");


// =============================================
// TIME
// =============================================

function getCurrentTime() {

    const now = new Date();

    return now.toLocaleTimeString();

}


// =============================================
// EVENT LOG
// =============================================

function addLog(message) {

    const logEntry =
        document.createElement("div");

    logEntry.className =
        "log-entry";


    const timeElement =
        document.createElement("span");

    timeElement.className =
        "log-time";

    timeElement.textContent =
        getCurrentTime();


    const messageElement =
        document.createElement("span");

    messageElement.className =
        "log-message";

    messageElement.textContent =
        message;


    logEntry.appendChild(timeElement);

    logEntry.appendChild(messageElement);


    eventLog.appendChild(logEntry);


    eventLog.scrollTop =
        eventLog.scrollHeight;

}


// =============================================
// CAMERA CONNECTED
// =============================================

cameraFeed.onload = function () {

    cameraError.classList.add("hidden");


    connectionText.textContent =
        "CONNECTED";


    streamStatus.textContent =
        "AI LIVE";


    streamIndicator.style.background =
        "#22c55e";

};


// =============================================
// CAMERA ERROR
// =============================================

cameraFeed.onerror = function () {

    connectionText.textContent =
        "DISCONNECTED";


    streamStatus.textContent =
        "OFFLINE";


    streamIndicator.style.background =
        "#ef4444";


    cameraError.classList.remove("hidden");


    addLog(
        "AI camera stream connection lost."
    );

};


// =============================================
// RECONNECT CAMERA
// =============================================

function reconnectCamera() {

    addLog(
        "Attempting to reconnect AI camera..."
    );


    cameraError.classList.add("hidden");


    connectionText.textContent =
        "CONNECTING";


    streamStatus.textContent =
        "CONNECTING";


    streamIndicator.style.background =
        "#f59e0b";


    // Reload Flask AI stream

    cameraFeed.src =
        "/video_feed?t=" + Date.now();

}


// =============================================
// GET PEOPLE DATA
// =============================================

async function updatePeopleData() {

    try {

        const response =
            await fetch(
                "/people?t=" + Date.now()
            );


        if (!response.ok) {

            throw new Error(
                "People API failed"
            );

        }


        const data =
            await response.json();


        // =====================================
        // PEOPLE COUNT
        // =====================================

        peopleCount.textContent =
            data.count;


        // =====================================
        // CROWD STATUS
        // =====================================

        crowdStatus.textContent =
            data.status;


        // Remove old status classes

        crowdStatus.classList.remove(
            "waiting",
            "normal",
            "moderate",
            "high",
            "critical"
        );


        // Add current class

        crowdStatus.classList.add(
            data.status.toLowerCase()
        );


        // =====================================
        // CAMERA STATUS
        // =====================================

        if (data.camera_connected) {

            streamStatus.textContent =
                "AI LIVE";

            streamIndicator.style.background =
                "#22c55e";

        }
        else {

            streamStatus.textContent =
                "OFFLINE";

            streamIndicator.style.background =
                "#ef4444";

        }


        // =====================================
        // CROWD MESSAGE
        // =====================================

        if (data.status === "NORMAL") {

            crowdMessage.textContent =
                "Crowd level is normal.";

        }

        else if (data.status === "MODERATE") {

            crowdMessage.textContent =
                "Moderate crowd detected.";

        }

        else if (data.status === "HIGH") {

            crowdMessage.textContent =
                "High crowd density detected.";

        }

        else if (data.status === "CRITICAL") {

            crowdMessage.textContent =
                "⚠️ Critical crowd level!";

        }

        else {

            crowdMessage.textContent =
                "Waiting for AI data...";

        }


    }
    catch (error) {

        console.error(
            "People API error:",
            error
        );

    }

}


// =============================================
// CLEAR LOGS
// =============================================

function clearLogs() {

    eventLog.innerHTML = "";

    addLog(
        "Event log cleared."
    );

}


// =============================================
// INITIALIZE DASHBOARD
// =============================================

function initializeDashboard() {

    addLog(
        "Starting Crowd Safety Monitor..."
    );


    addLog(
        "Connecting to AI processing server..."
    );


    addLog(
        "YOLO person detection enabled."
    );


    addLog(
        "Phone camera: 192.168.137.112:8080"
    );


    // Start API polling

    updatePeopleData();


    // Update every 1 second

    setInterval(
        updatePeopleData,
        1000
    );

}


// =============================================
// START
// =============================================

initializeDashboard();