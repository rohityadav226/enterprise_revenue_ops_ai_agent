from fastapi import FastAPI

# creating the fast api application
app = FastAPI(
    title="Enterprise Revenue OP's AI Agent",
    description="Backend for our ai assistant",
    version="1.0.0"
)

@app.get("/health")
def health_check():
    return {
        "status" : "Healthy",
        "message" : "Enterprise Rev Ops AI Agent API is Running"
    }

@app.get("/about")
def about_application():
    return {
        "application" : "Enterprise AI Agent" ,
        "version" : "1.0.0",
        "purpose" : "Business Automation"
    }

