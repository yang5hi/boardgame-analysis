# Dependencies
from types import new_class
import numpy as np
import pandas as pd
from flask import Flask, render_template, request,redirect, jsonify
from sqlalchemy import create_engine
import bgg_sql

# Create an instance of Flask
app = Flask(__name__)

# Create database connection
# change the owner name, password and port number based on your local situation
# engine = create_engine(f'postgresql://{*database_owner}:{*password}@localhost:{*port}/housing_db')
rds_connection_string = "postgres:Di2JieDu@n@localhost:5432/boardgame_db"
engine = create_engine(f'postgresql://{rds_connection_string}')

# =========================================================================================================
# read in csv file
game_info_df=pd.read_csv("data/boardgames_07022021.csv")
# remove duplicate games
game_info_df.drop_duplicates(subset=['objectid'], inplace=True)
# choose the features based on correlations
game_info_df=game_info_df[['average', 'numwanting', 'siteviews', 'blogs', 'minage', 'news',
                           'podcast', 'totalvotes', 'numcomments', 'numgeeklists', 'weblink']].copy()
# remove the rows which have invalid values
game_info_df.drop(game_info_df[game_info_df['average'] ==0].index, inplace = True)
game_info_df.drop(game_info_df[game_info_df['totalvotes'] ==0].index, inplace = True)
# drop the null rows
game_info_df.dropna(inplace=True)
# =========================================================================================================
# Set features (X) and target (y)
y=game_info_df['average']
X=game_info_df.drop(['average'],axis=1)
# Scale the data
from sklearn.preprocessing import MinMaxScaler
X_scaler = MinMaxScaler().fit(X)
X_scaled = X_scaler.transform(X)
# =========================================================================================================
from sklearn.ensemble import RandomForestRegressor
 # Create a random forest regressor,  n_estimators=100, criterion="mse", max_depth="None"
rf = RandomForestRegressor()
rf.fit(X_scaled, y)
# =========================================================================================================

app = Flask(__name__, static_url_path='/static')

RF_pred="  "
X_pred=[]

@app.route("/")
def home():
    print(f"home")
    news_df=pd.read_sql_query('select * from news', con=engine)
    game_info_df=pd.read_sql_query('select * from game_info', con=engine)
    ranking_200_df=pd.read_sql_query('select * from ranking_200', con=engine)
    news_dict=news_df.to_dict()
    game_info_dict=game_info_df.T.to_dict()
    ranking_200_df.set_index('BoardGameRank', inplace=True)
    ranking_dict=ranking_200_df.to_dict()
    bggData=[news_dict,game_info_dict,ranking_dict]
    # Return template and data
    return render_template("index.html", bggData=bggData, RF_pred=RF_pred[0],X_pred=X_pred)

@app.route("/prediction", methods=['POST','GET'])
def prediction():
    print(f"prediction")
    
    numwanting = request.form['numwanting']
    siteviews = request.form['siteviews']
    blogs = request.form['blogs']
    minage = request.form['minage']
    news = request.form['news']
    podcast = request.form['podcast']
    totalvotes = request.form['totalvotes']
    numcomments = request.form['numcomments']
    numgeeklists = request.form['numgeeklists']
    weblink = request.form['weblink']

    X_pred = np.array([[numwanting,siteviews, blogs, minage, news,
                podcast, totalvotes, numcomments, numgeeklists, weblink]])

    y_pred = rf.predict(X_pred)

    RF_pred = [round(y_pred[0], 2)]
    print(f'RF prediction= {RF_pred[0]}')
    print(X_pred[0])

    return render_template("index.html", RF_pred=RF_pred[0], X_pred=X_pred[0])

@app.route("/scrape")
def scraper():
    # Run the scrape function
    boardgame_data = bgg_sql.scrape()
    ranking_200_df=boardgame_data[0]
    game_info_selected_df=boardgame_data[1]
    news_df=boardgame_data[2]
    # Load dataframes into databases
    
    ranking_200_df.to_sql(name = 'ranking_200', con = engine, if_exists = 'replace', index = True)
    game_info_selected_df.to_sql(name = 'game_info', con = engine, if_exists = 'replace', index = True)
    news_df.to_sql(name = 'news', con = engine, if_exists = 'replace', index = False)
    # Redirect back to home page
    return redirect("/") #performing URL redirection
    
if __name__ == "__main__":
    app.run(debug=True)