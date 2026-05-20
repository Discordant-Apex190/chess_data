from fastapi import FastAPI


app = FastAPI()


@app.get("/games/{username}")
async def read_item(username):
    return {"username": username}


