Booking agent AI

BUISNESS CASE 
For traveling musicians booking performances is a key and challenging element of a successful career.  The most challenging problem is finding  suitable venues. For large acts this job is carried out by professional agents who charge as much as 20 percent of the booking price for their services. This is a price that smaller acts can not afford. As such they are left blindly googling around searching local music listings for venues and often missing key opportunities to make creative bookings.  
Building a recommender to aid in this search is a problem that modern data science techniques is tailor made for. 

DATA CHALLENGES
The first challenge in building a good recommender is finding a good data set. Most music venues that have live performances list there events in some sort of calendar. These calendars exist on private websites, facebook pages, third party websites and intermixed in newspaper websites. Most traveling performers have websites that list their tours in some form.  Unfortunately there is not a central database of all events all artists and all venues. 

There are several databases that come close Ticketmaster, Song-kick and Live-nation have national datasets but unfortunately they are mainly populated by the large events and performers. Band-camp has an impressive data set of artists but unfortunately there is no event or venue information. 

A website called BandsInTown has a data set that comes close to being perfect for this challenge.  They focus on helping artists promote their work and performances. As such they have an impressive list of artists and events. Each performer has a unique name and ID and every event has a unique ID unfortunately because artists are responsible for entering in their own tour information, venue information is not consistent.  One venue can have multiple name, a lat/lng can be present or not, there is no venue id and there is no contact information for the venue. Furthermore there is no descriptive information about the venue, i.e. size hours, ages, what kind of music the venue books.

GATHERING DATA
BandsInTown has a publicly two publicly available apis. Data was gathered with these API’s and web scraping. For more information about how this data was gathered please read the README in the BIT_Scraping folder.

DATA CLEANING AND FEATURE ENGINEERING
As mentioned BandsInTown has good information about the artists but little to no information about individual venues. Text data for the venues was made by combining all the text data for the artists that played at that venue. This process had to take place after doing any train test split. For more information about the preparing the data please look the the README in prep data folder.

TESTING
Recommenders are notoriously hard to test when dealing with implicit data. How do you know if a venue recomendation is of value to an artist. A survay of artists using the recomender would be the best approach, but not reasionable before launching a website. Because we will be recommending venues to artists it seams reasonable that if an artists plays a venue in the test data the model should return that venue in the top recommendations for that artist in the area where that venue exist. 

Using this logic the models were tested by selecting a event from the test set. Finding the hundred nearest venues to that event and testing the model for the that played that event and those 100 venues. If the model did not return the original venue in the top ten recommendations that was considered a failure. 

Three different models were tested. A multinomial, a collaborative filtering model and a simple model that just looked at the cosine similarity of the artists genre/bio info  against the venues genre/bio. 

RESULTS
Results of the testing clearly showed the looking at the cosine similarity of a the text data for a venue and a artists produced the best results. Results of these tests van be viewed in the slides folder. The results for the cosine similarity we so much better that I decided to force an artists looking for recomendations for venues to enter text data for there band if it was not present.

IMPLIMATION
To make recomendations for artists I mada a simple web app. The app asks for the name of the artists the the city and state where the artists is looking for a show and a radius in miles to look in. The app returns a list of venues ordered by there score. 

