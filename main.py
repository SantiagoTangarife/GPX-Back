from fastapi import FastAPI

from validations import Validations

app = FastAPI()
@app.get("/")
async def root():

    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}




file_path = "C:/Users/saxss/PycharmProjects/fastApiProject/stageExample (1).txt"
with open(file_path, 'r') as file:
    content = file.read()

#print(content)






rutagpx = "C:/Users/saxss/PycharmProjects/fastApiProject/Data/300 BRAYAN RICO.gpx"
validations_i= Validations()


resultado= validations_i.validations(content, rutagpx)



