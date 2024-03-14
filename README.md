# Crowd-Sourced Travel Planner Installation Guide
This guide provides detailed instructions for setting up and running the Crowd-Sourced Travel Planner application. Follow these steps to install the application and explore its features.

Or find the deployed app at: https://travel-planner-osu-capstone.wl.r.appspot.com/ 

# Prerequisites
Before you begin, ensure you have the following installed on your system:

* Python 3.8 or higher
* pip (Python package installer)
* Virtualenv (optional but recommended for creating isolated Python environments)

# Installation Steps

Clone the Crowd-Sourced Travel Planner repository to your local machine using the following command:

`git clone https://github.com/ernielum/Crowd-Sourced-Travel-Planner.git`

Navigate into the project directory:

`cd Crowd-Sourced-Travel-Planner`

**Set Up Virtual Environment (Optional)**

* Create a virtual environment to isolate the project dependencies:

`python3 -m venv env`

* Activate the virtual environment:

  * On macOS/Linux:

`source env/bin/activate`

  * On Windows:

`.\env\Scripts\activate`

**Install Dependencies**
*Install the required Python packages using pip:

`pip install -r requirements.txt`

**Configure Environment Variables**

* Create a .env file in the root directory of the project. You will need to fill in the values for the environment variables based on your specific configurations. Here is a template you can start with:

* Fill in the values with your specific configurations

`AUTH0_CLIENT_ID=your_auth0_client_id_here`

`AUTH0_CLIENT_SECRET=your_auth0_client_secret_here`

`AUTH0_DOMAIN=your_auth0_domain_here`

`APP_SECRET_KEY=your_app_secret_key_here`

`GOOGLE_MAPS_KEY=your_google_maps_api_key_here`

* Replace your_auth0_client_id_here, your_auth0_client_secret_here, etc., with your actual configuration values.

**Run the Application**

* Start the application by running:

`python main.py`

* You should see output indicating that the server is running, typically on http://127.0.0.1:8080.

# Accessing the Application

* After starting the application, open a web browser and navigate to http://127.0.0.1:8080 to access the Crowd-Sourced Travel Planner.

Alternatively, find the deployed app at: https://travel-planner-osu-capstone.wl.r.appspot.com/ 

# Features
* Select the Sign In button at the top right corner of the page
* Create a User profile by selecting the ‘sign up’ link
* Create and manage trips named after cities or events by entering the trip name and selecting ‘Create Trip’
* View the trip and pinned experiences by selecting the trip listed in the ‘My Trips’ page
* Search for experiences (restaurants, lodging, activities) on Google Maps and pin these experiences by selecting the pin icon in the pop-up info window
* Unpin experiences by selecting the unpin icon for that experience
* Rate locations by selecting the appropriate-level star rating and view crowd-sourced ratings located on to left side of the experience name and pins
* Re-center the map to previously pinned experiences by selecting the name of the experience listed in the pinned experiences list
* Edit trip names by selecting the pencil icon. When finished, select the pencil icon.
* Delete the entire trip by selecting the trash icon
* Sign out and return to the main user page


