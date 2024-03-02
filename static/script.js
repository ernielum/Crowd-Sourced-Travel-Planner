'use strict';

var map;

// Define an info window variable
var infoWindow = new google.maps.InfoWindow();

// Variable to store current tripId
var tripId;

// Variable to store experience from search
var experience;

// Initialize the map
function initMap() {
  // Specify the center coordinates for the map
  var centerCoordinates = { lat: 40.7128, lng: -74.0060 }; // Default to New York City

  // Create a new map instance and specify the map container
  map = new google.maps.Map(document.getElementById('map'), {
    center: centerCoordinates,
    zoom: 12 // Set default zoom level
  })

  // Initialize the Places Autocomplete service
  var input = document.getElementById('place-search');
  var autocomplete = new google.maps.places.Autocomplete(input);

  // Bias the search results to the map's viewport
  autocomplete.bindTo('bounds', map);
}

// Function to handle place search
function searchPlaces() {
  var input = document.getElementById('place-search').value;

  var request = {
    query: input,
    fields: ['geometry', 'place_id', 'name', 'formatted_address']
  };

  var service = new google.maps.places.PlacesService(map);

  service.findPlaceFromQuery(request, function(results, status) {
      if (status === google.maps.places.PlacesServiceStatus.OK && results && results.length) {
      
        experience = results

        var location = results[0].geometry.location;
        map.setCenter(location);
        map.setZoom(16);

        // Content to be displayed in infowindow
        var content = '<strong>' + results[0].name + '</strong><br>';
        content += results[0].formatted_address + '<br>';

        // Open the info window at the found location
        infoWindow.setContent(content);
        infoWindow.setPosition(location);
        infoWindow.open(map);

        // Show pin button after search
        document.getElementById('pin-button').style.display = 'block';

      } else {
          console.error('Place search failed:', status);
      }
  });
}

function pinExperience() {
  if (experience && tripId) {
    // Here you can send an AJAX request to your Flask backend to save the search results
    fetch('/experience_pin', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ tripId: tripId, experience: experience })
    })
    .then(response => {
      if (response.ok) {
        console.log('Experience pinned successfully');
        // Hide the pin button after successful pinning
        document.getElementById('pin-button').style.display = 'none';
        location.reload();
      } else {
        console.error('Failed to pin experience:', response.statusText);
      }
    })
    .catch(error => {
      console.error('Error:', error);
    });
  }

}

// Call initMap when the page has loaded
document.addEventListener('DOMContentLoaded', function() {
  initMap();
  tripId = document.getElementById('tripId').value;
});
