dummy_test_user_trips = [
    {"id": 1, "name": "Paris"},
    {"id": 2, "name": "Glacier National Park"},
    {"id": 3, "name": "Rome, Italy"},
    {"id": 4, "name": "Costa Rica"},
]

dummy_user_info = {"id": 1}

dummy_test_paris_experiences = [
    {   "id": 1,
        "name": "Eiffel Tower",
        "description": "Enjoy a thrilling trip to the Top and visit the entire Eiffel Tower accompanied by a guide \
            A tour of the Eiffel Tower is a thrilling and emotional experience. Accompanied by a member of the Eiffel Tower family \
                who is enamored with the monument, you will hear about momentous and everyday moments in its history, and learn \
                     more about the life of the Tower and the company that operates it, while visiting all three levels of the Tower. \
                        An unforgettable tour, available in French or English and lasting around 90 minutes, in groups of no more \
                            than 12 people! Your Official Eiffel Tower Guide will ensure that everything goes smoothly on your visit \
                                while helping you access the different levels, especially the elevators. And to enhance this experience,\
                                      the Eiffel Tower can offer you outstanding 10% discounts on a selection of products available in the\
                                          stores (Exclusive Eiffel Tower Collection) and certain restaurants (bistro on the First Floor and\
                                              the buffet on the esplanade). ",
        "location": "5 Avenue, Paris, FR 75007",
        "image": "",
        "avg_rating": "5",
        "user_rating": "5",
        "img_filepath": "/static/uploads/eiffel-tower.jpg"
    },
    {   "id": 2,
        "name": "The Louvre",
        "description": "The Louvre is a national art museum in Paris, France. It is home to the most canonical works of Western art including the Mona Lisa.",
        "location": "75001 Paris, France",
        "image": "",
        "avg_rating": "5",
        "user_rating": "5"
    },
    {   "id": 3,
        "name": "Seine River Cruise",
        "description": "",
        "location": "",
        "image": "",
        "avg_rating": "",
        "user_rating": ""
    }
]

dummy_test_glacier_experiences = [
    {   "id": 1,
        "name": "Bowman Lake",
        "description": "pass",
        "location": "",
        "image": "",
        "avg_rating": "5",
        "user_rating": "5"
    },
    {   "id": 2,
        "name": "Going to the Sun Road",
        "description": "pass",
        "location": "",
        "image": "",
        "avg_rating": "5",
        "user_rating": "5"
    },
    {   "id": 3,
        "name": "Trail of Cedars",
        "description": "",
        "location": "",
        "image": "",
        "avg_rating": "",
        "user_rating": ""
    }
]

dummy_test_rome_experiences = [
    {   "id": 1,
        "name": "Colosseum",
        "description": "pass",
        "location": "",
        "image": "",
        "avg_rating": "5",
        "user_rating": "5"
    },
    {   "id": 2,
        "name": "Vatican Museums",
        "description": "pass",
        "location": "",
        "image": "",
        "avg_rating": "5",
        "user_rating": "5"
    },
    {   "id": 3,
        "name": "St. Peter's Basilica",
        "description": "",
        "location": "",
        "image": "",
        "avg_rating": "",
        "user_rating": ""
    },
    {   "id": 4,
        "name": "Pantheon",
        "description": "pass",
        "location": "",
        "image": "",
        "avg_rating": "5",
        "user_rating": "5"
    },
    {   "id": 5,
        "name": "Piazza Navona",
        "description": "pass",
        "location": "",
        "image": "",
        "avg_rating": "5",
        "user_rating": "5"
    },
    {   "id": 6,
        "name": "Fontana dei Quattro Fiumi",
        "description": "pass",
        "location": "",
        "image": "",
        "avg_rating": "5",
        "user_rating": "5"
    }
]

dummy_test_experiences_data = []
dummy_test_experiences_data.extend(dummy_test_paris_experiences)
dummy_test_experiences_data.extend(dummy_test_glacier_experiences)
dummy_test_experiences_data.extend(dummy_test_rome_experiences)

dummy_test_trip_data = {
    "trip1": {
        "id": 1,
        "name": "Paris",
        "experiences": dummy_test_paris_experiences
    },
    "trip2": {
        "id": 2,
        "name": "Glacier National Park",
        "experiences": dummy_test_glacier_experiences
    },
    "trip3": {
        "id": 3,
        "name": "Rome",
        "experiences": dummy_test_rome_experiences
    },
    "trip4": {
        "id": 4,
        "name": "Costa Rica",
        "experiences": []
    }
}