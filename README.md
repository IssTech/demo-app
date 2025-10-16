# FastAPI + PostgreSQL Setup Guide (Ubuntu/Virtual Env with Docker DB)

This guide explains how to set up and test the provided FastAPI application locally using a Python virtual environment on Ubuntu, connecting to a PostgreSQL database running inside a Docker container.

## 1. Prerequisites

You must have the following installed on your Ubuntu system:

Python 3: (Usually pre-installed)

Docker: (You will need to be able to run the docker command.)

## 2. PostgreSQL Database Setup using a Single Docker Container

We will use a single docker run command to create and manage the PostgreSQL service.

Start the Database Container:
Navigate to your project directory and run the following command. This creates a container named **fastapi-postgres-db**, sets the necessary credentials, and maps the port to your host machine.

```
docker run --name fastapi-postgres-db \
-e POSTGRES_DB=fastapi_users_db \
-e POSTGRES_USER=postgres \
-e POSTGRES_PASSWORD=password \
-p 5432:5432 \
-v postgres_data:/var/lib/postgresql/data \
-d postgres:16-alpine
```

The container will be available on your host machine at `localhost:5432`.

Verify Database Readiness:
Wait a few seconds for the database to initialize. The application uses a retry logic to wait for the database, but you can manually check the status if needed:

docker logs fastapi-postgres-db
Look for a message indicating the database is ready for connections.


## 3. Python Virtual Environment Setup

It's best practice to isolate your project dependencies.

Navigate to your project directory.

Create a virtual environment:
```
python3 -m venv venv
```

Activate the environment:
```
source venv/bin/activate
```

(Your terminal prompt should now start with (venv))

## 4. Install Dependencies

Save the provided requirements.txt file in your project directory (if you haven't already).

Install the dependencies:
```
pip install -r requirements.txt
```

## 5. Run the FastAPI Application

Save the provided main.py file in your project directory.

Start the server:
The application will connect to the Postgres container running on localhost:5432.
```
uvicorn main:app --reload
```

The server will start running, typically at `http://127.0.0.1:8000`.

## 6. Testing the API (CRUD Operations)

You can test all the functionality directly in your browser using the interactive documentation provided by FastAPI (Swagger UI).

Open the Docs: Go to `http://127.0.0.1:8000/docs` in your web browser.

Populate the Database (C - Seeder):

Find the POST `/populate_50` endpoint.

Click "Try it out" and then "Execute".

You should receive a 201 status code and a message confirming 50 users were added. This data is now persistent inside your Docker volume.

Read All Data (R):

Find the GET `/users/` endpoint.

Click "Try it out" and then "Execute".

The response body will show a JSON list of all 50 generated users, confirming your connection to the Dockerized database works.

Create a Single User (C):

Find the POST `/users/` endpoint.

Click "Try it out" and replace the example body with your custom data:
```
{
  "firstname": "John",
  "lastname": "Doe",
  "zip_code": "10001",
  "country": "USA"
}
```

Execute. Note the id of the newly created user (e.g., 51).

Modify a User (U):

Find the PUT `/users/{user_id}` endpoint.

Click "Try it out", enter the id from step 4 (e.g., 51) in the path parameter, and update the body:
```
{
  "firstname": "Jane",
  "lastname": "Doe",
  "zip_code": "90210",
  "country": "USA"
}
```

Execute and verify the user data is updated.

Remove a User (D):

Find the DELETE `/users/{user_id}` endpoint.

Click "Try it out", enter the id (e.g., 51), and execute.

The status code should be 204 No Content. Verify by trying to GET `/users/51` which should return a 404 Not Found.

## 7. Stopping the Server and Deactivating the Environment

Stop the FastAPI Server: Press Ctrl+C in the terminal where uvicorn is running.

Stop the Docker Container: Stop and remove the database container (the data remains saved in the local volume):
```
docker stop fastapi-postgres-db
docker rm fastapi-postgres-db
```

Deactivate the Environment:
```
deactivate
```