In order to make predictions I need several different types of data. I need a database of all artists, I need a database of all venues and need a database of all events.

Building artists_df
The artists database is made by converting the information gathered in the mongodb to a pandas dataframe.  This data frame is pickled rather then saved to a csv file in order to preserve the structure of the list in the tours column. 

Building the events_raw_df
The events_raw_df is important in testing of our models. It needs to contain the artists_genre and artists_bio info of the artists that play the events.  The venues need to have a unique ids and unique lat/lng but the venue bio and genre should absent. This is because the text data for a venue is composed of all the artists that have played at that venue and that needs to be generated after we do any splits. 

Fixing the Venue Names
Initially the events_raw_df is made by expanding the tours list of the artists_df. Doing this I get a  list of events with artists ids that are unique and venue names that are not unique. Because the venue names were entered by the artist playing the event, we have names like “The Showbox”, “Showbod in Seattle”, and “The kinks at the Showbox in seattle”.  

To clean this information a library called fuzzywuzzy was used.  Fuzzywuzzy compares two phrases and gives a score on their similarity. To map varied venue names to a distinct venue name I used a dictionary. This dictionary was built by first ordering the original venue names in each city from shortest to longest. The shortest name in this list was then compared against all other names in the list of original venue names, any name that gets a fuzzywuzzy score above a threshold of 87 was put into the dictionary as a key, it’s value is the shortest name that I used to find it. Now all venue names that mapped to this short name and the short name are removed from the sorted list of original venue names 

This processes consolidated the venue names to a half their original size. It is not perfect and in final implementation this step should be refined.  In the end it might be necessary to have  a combination of human and machine processing to clean these venue names. 

Also in the events_df_raw I added a column called venue_identifier it is simply the unique-ish venue name with the city and state. This column is later used when making a events_df  

Building a venues_df
Now that each venue has a unique-ish name I am ready to use the events_df_raw to make a venues_df. I do this by the grouping the events on the city state and unique_is venue name, the artists_bio and artists_genres are joined together to make a venue_genre and venue_bio and the lat/lng is averaged. There were a handful of venue still without lat/lng so I dropped them. This df in given an index which is venue_id.


Building a events_df. 

Now that we have a venues_df we are ready to make the events_df. I do this by joining the venues df with the events_raw_df on the venue_identifier. In doing this we give the events_df venue id and consistent venue lat/lng

Making a new events_df_raw
Finaly I fix the events_df_raw so that it has unique venue_ids and the lat/lng is all cleaned up. When we split the data we do so on the dataframe and then repeat the steps above to make a train data set. 

All these steps can be using the functions in generate_tables.py. Running the notebook in this file does this in a step by step fashion. 
 