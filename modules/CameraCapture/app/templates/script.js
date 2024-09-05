var currentimg = document.getElementById("currentImage");
// var binaryimg = document.getElementById("binaryImage");
var processedimg = document.getElementById("processedImage");
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

    // Update the form fields with the values from the JSON data
    const localDetectionsField = document.getElementById('local-detections');
    const remoteDetectionsField = document.getElementById('remote-detections');
    const promptResponseField = document.getElementById('prompt-response');

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

//Establish WebSocket connection for the current images
var currentImageSocket = new WebSocket("ws://" + location.host + "/currentimage");

// Handle incoming "current" images
currentImageSocket.onmessage = function(event) {
  if (event.data instanceof Blob) {
      // // Get the existing image element by its ID
      const currentimg = document.getElementById('currentImage');
      
      // Create an object URL from the Blob and set it as the src of the image
      currentimg.src = URL.createObjectURL(event.data);

      // Optionally, manage memory by revoking the object URL once the image is loaded
      currentimg.onload = () => {
          URL.revokeObjectURL(currentimg.src); // Clean up the object URL to release memory
          currentImageSocket.send("next");
      };
  }
}

currentImageSocket.onopen = function() {
  console.log("connection was established for current images");
  currentImageSocket.send("next");
};

// // Once an image has been refreshed this code will fire and request another 
// binaryimg.onload = function() {
//   URL.revokeObjectURL(binaryimg.src); // Clean up the object URL to release memory
//   processedImageSocket.send("next");
// }

// Establish WebSocket connection for processed images
var processedImageSocket = new WebSocket("ws://" + location.host + "/processedimage");

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

// // Once an image has been refreshed this code will fire and request another 
// processedImageSocket.onload = function() {
//   ws.send("next");
// }

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

document.addEventListener('DOMContentLoaded', function () {
    
    // Send an update to state when any value changes
    const inputs = [
        rectificationTopLeftX, rectificationTopLeftY,
        rectificationTopRightX, rectificationTopRightY,
        rectificationBottomLeftX, rectificationBottomLeftY,
        rectificationBottomRightX, rectificationBottomRightY,
        convertToGrayCheckbox, performRectificationCheckbox, removeBackgroundCheckbox
    ];

    // Add event listeners to each input element
    inputs.forEach(input => {
        input.addEventListener('change', dispatchState);  // use 'input' or 'change' if you prefer
    });

    // Check if any of the elements are not found
    // if (!presetsDropdown) console.error('Element with ID "presets" not found.');
    // if (!localEndpointInput) console.error('Element with ID "local-endpoint" not found.');
    // if (!cloudEndpointInput) console.error('Element with ID "cloud-endpoint" not found.');
    // if (!resizeWidthInput) console.error('Element with ID "resize-width" not found.');
    // if (!waitTimeInput) console.error('Element with ID "wait-time" not found.');
    // if (!resizeHeightInput) console.error('Element with ID "resize-height" not found.');
    // if (!convertGrayCheckbox) console.error('Element with ID "convert-gray" not found.');
    // if (!processLocallyCheckbox) console.error('Element with ID "process-locally" not found.');
    // if (!processRemotelyCheckbox) console.error('Element with ID "process-remotely" not found.');
    // if (!sendLocalToHubCheckbox) console.error('Element with ID "send-local-to-hub" not found.');
    // if (!sendRemoteToHubCheckbox) console.error('Element with ID "send-remote-to-hub" not found.');
    // if (!showLocalDetections) console.error('Element with ID "show-local-detections" not found.');
    // if (!showRemoteDetections) console.error('Element with ID "show-remote-detections" not found.');

    convertToGrayCheckbox.checked = false;
    performRectificationCheckbox.checked = false;
    removeBackgroundCheckbox.checked = false;
    rectificationTopLeftX.value = 670; 
    rectificationTopLeftY.value = 0; 
    rectificationTopRightX.value = 1260; 
    rectificationTopRightY.value = 0; 
    rectificationBottomLeftX.value = 710; 
    rectificationBottomLeftY.value = 720; 
    rectificationBottomRightX.value = 1280; 
    rectificationBottomRightY.value = 680; 

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
                    resizeWidthInput.value = '1280'; // Use original image size
                    resizeHeightInput.value = '720'; 
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
                    resizeWidthInput.value = '1280'; // Use original image size
                    resizeHeightInput.value = '720'; 
                    waitTimeInput.value = 0.1; // No costs
                    processLocallyCheckbox.checked = true;
                    processRemotelyCheckbox.checked = false;
                    sendLocalToHubCheckbox.checked = false;
                    sendRemoteToHubCheckbox.checked = false;
                    showLocalDetections.checked = true;
                    showRemoteDetections.checked = false;
                    break;
            }
        });
    }

    // Set the default value to edge
    presetsDropdown.value = 'edge';  // Set this to the value you want to select
    // Trigger the 'change' event to load form data from this selection
    const event = new Event('change');
    presetsDropdown.dispatchEvent(event);

    // Add event listeners to play/pause buttons
    const updateButton = document.getElementById('update-button');

    updateButton.addEventListener('click', function () {
        dispatchState()
    });

});

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

