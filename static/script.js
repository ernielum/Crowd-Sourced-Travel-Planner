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
  var defaultZoom = 12; // Set default zoom level

  // Check if there are saved coordinates in local storage
  var savedCoordinates = localStorage.getItem('mapCoordinates');
  if (savedCoordinates) {
    centerCoordinates = JSON.parse(savedCoordinates);
  }

  // Check if there is saved zoom level in local storage
  var savedZoom = localStorage.getItem('mapZoom');
  if (savedZoom) {
    defaultZoom = JSON.parse(savedZoom);
  }

  // Create a new map instance and specify the map container
  map = new google.maps.Map(document.getElementById('map'), {
    center: centerCoordinates,
    zoom: defaultZoom
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
    fields: ['name', 'formatted_address', 'place_id', 'geometry', 'rating']
  };

  var service = new google.maps.places.PlacesService(map);

  service.findPlaceFromQuery(request, function(results, status) {
    if (status === google.maps.places.PlacesServiceStatus.OK && results && results.length) {
      experience = results[0]; // Save the place details globally for use in pinExperience
      var place = results[0];
      var location = place.geometry.location;

      map.setCenter(location);
      map.setZoom(16);

      var ratingDisplay = place.rating ? "Google Rating: " + place.rating : "Rating not available";

      var content = '<div style="color: var(--black); font-family: Roboto, sans-serif;">' +
        '<strong style="font-size: 16px; display: block; margin-bottom: 2px;">' + place.name + '</strong><br>' +
        place.formatted_address + '<br>' +
        (place.rating ? 'Google rating: ' + place.rating : 'Google rating not available') +
        '</div>' +
        '<div style="text-align: center; margin-top: 5px;">' + // Center pin button and add space
        '<button onclick="pinExperience()" id="pin-button" ' +
        'style="display: inline-block; margin: 10px auto; padding: 5px 10px; background-color: var(--dark); color: var(--white); border: none; border-radius: 20px; cursor: pointer;">' +
        '<span class="material-symbols-outlined" style="vertical-align: middle;">keep</span> Pin' +
        '</button>' +
        '</div>';

      infoWindow.setContent(content);
      infoWindow.setPosition(location);
      infoWindow.open(map);

    } else {
      console.error('Place search failed:', status);
    }
  });
}

function pinExperience() {
  // Save the new center coordinates to local storage
  var center = map.getCenter();
  localStorage.setItem('mapCoordinates', JSON.stringify({ lat: center.lat(), lng: center.lng() }));

  // Save the new zoom level to local storage
  var zoom = map.getZoom();
  localStorage.setItem('mapZoom', zoom.toString());

  if (experience && tripId) {
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


/**********************************************************
 * Center a pinned Experience on the map
 * 
 *********************************************************/
// Function to center a pinned Experience on the map
function findExperience(place_id) {
  var input = place_id;

  var request = {
    query: input,
    fields: ['geometry', 'place_id', 'name', 'formatted_address', 'rating']
  };

  var service = new google.maps.places.PlacesService(map);

  service.findPlaceFromQuery(request, function(results, status) {
    if (status === google.maps.places.PlacesServiceStatus.OK && results && results.length) {
      var place = results[0];
      var location = place.geometry.location;
      map.setCenter(location);
      map.setZoom(16);

      // Constructing content with inline styles
      var content = '<div style="font-family: Roboto, Arial, sans-serif; color: var(--black);">' +
        '<strong style="font-size: 16px; margin-bottom: 5px;">' + place.name + '</strong><br>' +
        '<span style="font-size: 14px;">' + place.formatted_address + '</span><br>' +
        '<span style="font-size: 14px;">' + (place.rating ? 'Google rating: ' + place.rating : 'Google rating not available') + '</span>' +
        '</div>' +
        '<div style="text-align: center; margin-top: 5px;">';

      infoWindow.setContent(content);
      infoWindow.setPosition(location);
      infoWindow.open(map);
    } else {
      console.error('Place search failed:', status);
    }
  });
}


/**********************************************************
 * Display and Update Rating
 * Dynamic User Rating Script (includes hover effect)
 *********************************************************/
function ratings() {
  const stars = document.querySelectorAll('#user-rating .user-star');
  let ratingValue = document.getElementById('userRatingValue').value;
  const form = document.getElementById('rate-experience'); // Reference to the form

  const updateRatingDisplay = (rating) => {
    stars.forEach((star, index) => {
      star.classList.toggle('full-star', index < rating);
      star.classList.toggle('empty-star', index >= rating);
    });
  };

  stars.forEach((star, index) => {
    // Preview rating on hover
    star.addEventListener('mouseover', () => updateRatingDisplay(index + 1));

    // Set rating on click and submit form
    star.addEventListener('click', () => {
      const rating = index + 1;
      var user_rating = 0;
      // calculate rating from total star indices (modulus 5)
      user_rating = rating % 5;
      // account for ratings of 5, set to 5 rather than 0
      if (user_rating == 0) {
        user_rating = 5;
      }
      document.getElementById('userRatingValue').value = user_rating; // Update hidden input with the rating
      updateRatingDisplay(rating);

      // Get the parent form of the clicked star
      const parentForm = star.closest('.rate-form');
      // Get the experienceId associated with the parent form
      const experienceId = parentForm.querySelector('input[name="experienceId"]').value;
      // Update the hidden input with the experienceId
      form.querySelector('input[name="experienceId"]').value = experienceId;

      // Submit the form
      form.submit();

    });

    // Reset preview on mouse out to reflect actual selected rating
    star.addEventListener('mouseleave', () => updateRatingDisplay(ratingValue));
  });

  // Reset to actual rating when not hovering over the stars
  document.getElementById('user-rating').addEventListener('mouseleave', () => {
    updateRatingDisplay(ratingValue);
  });
}

// Call initMap when the page has loaded
document.addEventListener('DOMContentLoaded', function () {
  initMap();
  tripId = document.getElementById('tripId').value;
  ratings();
});

/**********************************************************
 * Edit a Trip
 * Update trip name and save in database
 *********************************************************/

        function editTripName() {
            var display = document.getElementById('trip-name-display');
            var editField = document.getElementById('trip-name-edit');
            var isEditing = editField.style.display === 'none';

            if (isEditing) {
                // Switch to edit mode
                display.style.display = 'none';
                editField.style.display = '';
                editField.focus();
            } else {
                // Save changes if we're already in edit mode
                saveTripName(editField.value);
            }
        }

        function saveTripName(newName) {
            var tripId = document.getElementById('edit-trip-button').value;
            fetch('/trip_edit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ tripId: tripId, newName: newName }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Update the display with the new name and switch back to display mode
                    document.getElementById('trip-name-display').textContent = newName;
                    document.getElementById('trip-name-display').style.display = '';
                    document.getElementById('trip-name-edit').style.display = 'none';
                } else {
                    console.error('Error updating trip name:', data.message);
                }
            })
            .catch(error => console.error('Error:', error));
        }
 
