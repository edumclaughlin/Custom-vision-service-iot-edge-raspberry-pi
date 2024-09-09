document.addEventListener('DOMContentLoaded', function () {

    // References to DOM objects
    var presetsDropdown = document.getElementById('presets');
    var localEndpointInput = document.getElementById('local-endpoint');
    var cloudEndpointInput = document.getElementById('cloud-endpoint');
    var resizeWidthInput = document.getElementById('resize-width');
    var resizeHeightInput = document.getElementById('resize-height');
    var waitTimeInput = document.getElementById('wait-time');
    var processLocallyCheckbox = document.getElementById('process-locally');
    var processRemotelyCheckbox = document.getElementById('process-remotely');
    var sendLocalToHubCheckbox = document.getElementById('send-local-to-hub');
    var sendRemoteToHubCheckbox = document.getElementById('send-remote-to-hub');
    var showLocalDetections = document.getElementById('show-local-detections');
    var showRemoteDetections = document.getElementById('show-remote-detections');

    var convertToGrayCheckbox = document.getElementById('convert-gray');
    var performRectificationCheckbox = document.getElementById('perform-rectification');
    var removeBackgroundCheckbox = document.getElementById('remove-background');
    var rectificationTopLeftX = document.getElementById('rectification-topleftx'); 
    var rectificationTopLeftY = document.getElementById('rectification-toplefty'); 
    var rectificationTopRightX = document.getElementById('rectification-toprightx'); 
    var rectificationTopRightY = document.getElementById('rectification-toprighty'); 
    var rectificationBottomLeftX = document.getElementById('rectification-bottomleftx'); 
    var rectificationBottomLeftY = document.getElementById('rectification-bottomlefty'); 
    var rectificationBottomRightX = document.getElementById('rectification-bottomrightx'); 
    var rectificationBottomRightY = document.getElementById('rectification-bottomrighty'); 

    var localDetectionsField = document.getElementById('local-detections');
    var remoteDetectionsField = document.getElementById('remote-detections');
    var promptResponseField = document.getElementById('prompt-response');

    var displayimg = document.getElementById("displayImage");
    var processedimg = document.getElementById("processedImage");

    // The /stream web-socket will exchange form state with the server and respond to messages
    var ws = new WebSocket("ws://" + location.host + "/stream");

    ws.onopen = function() {
        console.log("connection was established");
        dispatchState()
    };

    // Any server-side updates are notified via a json object 
    ws.onmessage = function(event) {
        console.log(`Received message: ${event.data}`);

        // Parse the JSON data
        const data = JSON.parse(event.data);

        // If the data for each field is a JSON object or array, convert it to a string
        localDetectionsField.value = data.local_detections !== undefined
            ? (typeof data.local_detections === 'object' 
                ? JSON.stringify(data.local_detections, null, 2) 
                : data.local_detections)
            : 'No local detections'; // Provide a default value if undefined

        remoteDetectionsField.value = data.remote_detections !== undefined
            ? (typeof data.remote_detections === 'object' 
                ? JSON.stringify(data.remote_detections, null, 2) 
                : data.remote_detections)
            : 'No remote detections'; // Provide a default value if undefined

        promptResponseField.value = data.prompt_response !== undefined
            ? (typeof data.prompt_response === 'object' 
                ? JSON.stringify(data.prompt_response, null, 2) 
                : data.prompt_response)
            : 'No prompt response'; // Provide a default value if undefined
    };

    //Establish WebSocket connection for the display images (Camera view)
    var displayImageSocket = new WebSocket("ws://" + location.host + "/displayimage");

    // Handle incoming display images (For camera view)
    displayImageSocket.onmessage = function(event) {
        if (event.data instanceof Blob) {
            // // Get the existing image element by its ID
            const displayimg = document.getElementById('displayImage');
            
            // Create an object URL from the Blob and set it as the src of the image
            displayimg.src = URL.createObjectURL(event.data);

            // Optionally, manage memory by revoking the object URL once the image is loaded
            displayimg.onload = () => {
                URL.revokeObjectURL(displayimg.src); // Clean up the object URL to release memory
                displayImageSocket.send("next");
            };
        }
    }

    displayImageSocket.onopen = function() {
        console.log("connection was established for camera images");
        displayImageSocket.send("next");
    };

    // Establish WebSocket connection for processed images (Detections View)
    var processedImageSocket = new WebSocket("ws://" + location.host + "/processedimage");

    // Handle incoming processed images (For detections view)
    processedImageSocket.onmessage = function(event) {
        if (event.data instanceof Blob) {
            // Get the existing image element by its ID
            const processedimg = document.getElementById('processedImage');
            
            // Create an object URL from the Blob and set it as the src of the image
            processedimg.src = URL.createObjectURL(event.data);

            // Optionally, manage memory by revoking the object URL once the image is loaded
            processedimg.onload = () => {
                URL.revokeObjectURL(processedimg.src); // Clean up the object URL to release memory
                processedImageSocket.send("next");
            };
        }
    }

    processedImageSocket.onopen = function() {
        console.log("connection was established for processed images");
        processedImageSocket.send("next");
    };

    // Send an update to state when any value changes
    const inputs = [
        rectificationTopLeftX, rectificationTopLeftY,
        rectificationTopRightX, rectificationTopRightY,
        rectificationBottomLeftX, rectificationBottomLeftY,
        rectificationBottomRightX, rectificationBottomRightY,
        convertToGrayCheckbox, performRectificationCheckbox, removeBackgroundCheckbox,
        //presetsDropdown, 
        localEndpointInput, cloudEndpointInput,
        resizeWidthInput, resizeHeightInput, 
        waitTimeInput, processLocallyCheckbox, processRemotelyCheckbox, 
        sendLocalToHubCheckbox, sendRemoteToHubCheckbox, 
        showLocalDetections, showRemoteDetections
    ];

    // Add event listeners to each input element
    inputs.forEach(input => {
        input.addEventListener('change', dispatchState);  // use 'input' or 'change' if you prefer
    });


    convertToGrayCheckbox.checked = false;
    performRectificationCheckbox.checked = false;
    removeBackgroundCheckbox.checked = false;
    rectificationTopLeftX.value = 790; 
    rectificationTopLeftY.value = 0; 
    rectificationTopRightX.value = 1240; 
    rectificationTopRightY.value = 0; 
    rectificationBottomLeftX.value = 850; 
    rectificationBottomLeftY.value = 720; 
    rectificationBottomRightX.value = 1280; 
    rectificationBottomRightY.value = 620; 

    if (presetsDropdown) {
        presetsDropdown.addEventListener('change', function () {
            const selectedPreset = presetsDropdown.value;

            // Set values based on the selected preset
            switch (selectedPreset) {
                case 'llama-llava':
                    localEndpointInput.value = 'http://object-detection-service:80/image';
                    cloudEndpointInput.value = 'http://192.168.2.21:7071/api/AnalyzeImage/llama';
                    resizeWidthInput.value = 672; // Must match model input-layer
                    resizeHeightInput.value = 672; 
                    waitTimeInput.value = 5; // No external hosts for such models
                    processLocallyCheckbox.checked = true;
                    processRemotelyCheckbox.checked = true;
                    sendLocalToHubCheckbox.checked = false;
                    sendRemoteToHubCheckbox.checked = false;
                    showLocalDetections.checked = false;
                    showRemoteDetections.checked = false;
                    break;
                
                case 'gpt-4o':
                    localEndpointInput.value = 'http://object-detection-service:80/image';
                    cloudEndpointInput.value = 'http://192.168.2.21:7071/api/AnalyzeImage/OpenAI';
                    resizeWidthInput.value = 672; 
                    resizeHeightInput.value = 672; 
                    waitTimeInput.value = 3; // Costs are high for these models currently
                    processLocallyCheckbox.checked = true;
                    processRemotelyCheckbox.checked = false;
                    sendLocalToHubCheckbox.checked = false;
                    sendRemoteToHubCheckbox.checked = false;
                    showLocalDetections.checked = false;
                    showRemoteDetections.checked = false;
                    break;
                
                case 'product-detection':
                    localEndpointInput.value = 'http://object-detection-service:80/image';
                    cloudEndpointInput.value = 'http://192.168.2.21:7071/api/AnalyzeImage/Azure';
                    resizeWidthInput.value = 0; // Use original image size
                    resizeHeightInput.value = 0; 
                    waitTimeInput.value = 30; // The product detection API costs circa £3.893/1K transactions
                    processLocallyCheckbox.checked = true;
                    processRemotelyCheckbox.checked = true;
                    sendLocalToHubCheckbox.checked = false;
                    sendRemoteToHubCheckbox.checked = true;
                    showLocalDetections.checked = false;
                    showRemoteDetections.checked = true;
                    break;
                
                case 'edge':
                    localEndpointInput.value = 'http://object-detection-service:80/image';
                    cloudEndpointInput.value = '';
                    resizeWidthInput.value = 0; // Use original image size
                    resizeHeightInput.value = 0; 
                    waitTimeInput.value = 0.1; // No costs
                    processLocallyCheckbox.checked = true;
                    processRemotelyCheckbox.checked = false;
                    sendLocalToHubCheckbox.checked = false;
                    sendRemoteToHubCheckbox.checked = false;
                    showLocalDetections.checked = true;
                    showRemoteDetections.checked = false;
                    break;
            }

            //dispatchState();
        });
    }

    // Set the default value to edge
    presetsDropdown.value = 'edge';  // Set this to the value you want to select
    // Trigger the 'change' event to load form data from this selection
    const event = new Event('change');
    presetsDropdown.dispatchEvent(event);

    function dispatchState() {
        // Serialize the form data into a JSON object
        const formData = {
            localEndpoint: localEndpointInput.value,
            cloudEndpoint: cloudEndpointInput.value,
            resizeWidth: resizeWidthInput.value,
            resizeHeight: resizeHeightInput.value,
            waitTime: waitTimeInput.value,
            processLocally: processLocallyCheckbox.checked,
            processRemotely: processRemotelyCheckbox.checked,
            sendLocalToHub: sendLocalToHubCheckbox.checked,
            sendRemoteToHub: sendRemoteToHubCheckbox.checked,
            showLocalDetections: showLocalDetections.checked,
            showRemoteDetections: showRemoteDetections.checked,
    
            convertToGray: convertToGrayCheckbox.checked,
            removeBackground: removeBackgroundCheckbox.checked,
            performRectification: performRectificationCheckbox.checked,
            rectificationTopLeftX: rectificationTopLeftX.value,
            rectificationTopLeftY: rectificationTopLeftY.value,
            rectificationTopRightX: rectificationTopRightX.value,
            rectificationTopRightY: rectificationTopRightY.value,
            rectificationBottomLeftX: rectificationBottomLeftX.value,
            rectificationBottomLeftY: rectificationBottomLeftY.value,
            rectificationBottomRightX: rectificationBottomRightX.value,
            rectificationBottomRightY: rectificationBottomRightY.value,
        };
    
        const jsonData = JSON.stringify(formData, null, 2); // Pretty print with 2 spaces
        ws.send(jsonData)
    }

    // Page tabs
    function openTab(tabId) {
        // Hide all tab contents
        var tabContents = document.querySelectorAll('.tab-content');
        tabContents.forEach(function(tabContent) {
            tabContent.classList.remove('active');
        });

        // Remove active class from all tabs
        var tabs = document.querySelectorAll('.tab');
        tabs.forEach(function(tab) {
            tab.classList.remove('active');
        });

        // Show the selected tab and set it as active
        document.getElementById(tabId).classList.add('active');
        event.currentTarget.classList.add('active');
    }

    // Determine pixel co-ordinates within image
    const coordsDisplay = document.getElementById('coords');

    var currentCorner = 1
    // Attach a click event listener to the image
    displayimg.addEventListener('click', function(event) {
        // Get the position of the image relative to the viewport
        const rect = displayimg.getBoundingClientRect();
        
        // Calculate the x, y coordinates relative to the image itself
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        // Display the coordinates    
        switch (currentCorner) {
            case 1:
                rectificationTopLeftX.value = Math.round(x);
                rectificationTopLeftY.value = Math.round(y);
            case 2:
                rectificationTopRightX.value = Math.round(x);
                rectificationTopRightY.value = Math.round(y);
            case 3:
                rectificationBottomRightX.value = Math.round(x);
                rectificationBottomRightY.value = Math.round(y);
            case 4:
                rectificationBottomLeftX.value = Math.round(x);
                rectificationBottomLeftY.value = Math.round(y);
        }
        currentCorner = currentCorner >= 4 ? 1 : currentCorner + 1;
        console.log(`X: ${Math.round(x)}, Y: ${Math.round(y)}`)
    }); 
});
