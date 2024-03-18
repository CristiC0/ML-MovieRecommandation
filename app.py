# -*- coding: utf-8 -*-

from flask import Flask
from flask_restful import Resource, Api, reqparse
import pandas as pd
import numpy as np
from Modules.userRequestedFor import userRequestedFor
from Modules.dataEngineering import dataEngineering
from Modules.loadRequirements import loadRequirements
from Modules.kmeansModel import kmeansModel
from Modules.saveLoadFiles import saveLoadFiles
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
api = Api(app)

def flatten_list(nested_list):
    flattened_list = []
    for element in nested_list:
        if isinstance(element, list):
            flattened_list.extend(flatten_list(element))
        else:
            flattened_list.append(element)
    return flattened_list

class GetAllMovieIDs(Resource):
    def get(self):
        movies=saveLoadFiles().loadClusterMoviesDataset()

        moviesIds=[]
        for i in range(len(movies)):
            moviesIds.append(list(movies[i]['movieId']))
        
        moviesIds=map(lambda x:str(x), list(set(flatten_list(moviesIds))))
        
        movies_metadata = pd.read_csv('./Movies Data/movies_metadata.csv', 
        usecols = ['id', 'genres', 'original_title', 'poster_path',]).dropna()
        
        mask= movies_metadata['id'].isin(moviesIds)
        response=movies_metadata[mask]
       
        return {'movies': response.values.tolist()}, 200, {'Access-Control-Allow-Origin': '*'} 

class GetMovieInfos(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('movie_ids',action='append', required=True, help='No movie ids provided', location='json')

    def post(self):
        args = self.reqparse.parse_args()
        movie_ids = args['movie_ids']
        movie_ids=list(map(lambda x:str(x), movie_ids))
        print(movie_ids)
        movies_metadata = pd.read_csv('./Movies Data/movies_metadata.csv', 
        usecols = ['id', 'genres', 'original_title', 'poster_path',]).dropna()

        mask= movies_metadata['id'].isin(movie_ids)
        response=movies_metadata[mask]
       
        return {'movies': response.values.tolist()}, 200, {'Access-Control-Allow-Origin': '*'}       

class GetMoviesForUser(Resource):
    def get(self, user_id):
        if int(user_id) is user_id:
            users_data = dataEngineering().loadUsersData()
            if users_data[0]:
                if user_id not in users_data[1]['users_list']:
                    print('API Get Request: By Invalid userId: ', user_id)
                    return [False, 'Invalid User ID']
                else:
                    print('API Get Request: By userId: ', user_id)
                    return userRequestedFor(user_id, users_data[1]['users_data'], making_recommendations = True).recommendMostFavouriteMovies(), 200, {'Access-Control-Allow-Origin': '*'} 
            else:
                return users_data
            
class trainModel(Resource):
    def put(self):
        kmeans = kmeansModel()
        trained_data = kmeans.run_model()
        print(trained_data)
        if trained_data[0]:
            saving_files = kmeans.saveFiles()
            if saving_files[0]:
                return [True, 'Training completed and saved successfully'], 201, {'Access-Control-Allow-Origin': '*'} 
            else:
                saving_files[1]

class AddUserWithRatings(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('user_id', type=int, required=True, help='No user_id provided', location='json')
        self.reqparse.add_argument('ratings',action='append', required=True, help='No ratings provided', location='json')

    def post(self):
        id=500
        args = self.reqparse.parse_args()
        user_id = args['user_id']
        ratings = args['ratings']
       
        f = open("./Movies Data/ratings.csv", "a")

        for movieId in ratings:
            f.write("\n"+str(id)+","+str(user_id)+","+movieId+",4.5")
            id+=1
            
        f.close()
        
        return {'message': 'User added successfully'}, 201, {'Access-Control-Allow-Origin': '*'} 

api.add_resource(GetAllMovieIDs, '/movies')
api.add_resource(trainModel, '/training')
api.add_resource(GetMoviesForUser, '/<int:user_id>')
api.add_resource(AddUserWithRatings, '/add_user')
api.add_resource(GetMovieInfos, '/movie_infos')
app.run(port=2000)