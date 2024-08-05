from azure.storage.blob import BlobServiceClient, PublicAccess

# Connection string for Azurite
connection_string = "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNoAHo/NgB3VWAxFfJZ7ZZan=somekey;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"

# Initialize the BlobServiceClient
blob_service_client = BlobServiceClient.from_connection_string(connection_string)


# Function to create a container
def create_container(container_name, public_access=None):
    try:
        blob_service_client.create_container(
            container_name, public_access=public_access
        )
        print(
            f"Container '{container_name}' created with public access: {public_access}"
        )
    except Exception as e:
        if "ContainerAlreadyExists" in str(e):
            print(f"Container '{container_name}' already exists.")
        else:
            raise e


# Create public container
create_container("facility-container", public_access=PublicAccess.Container)

# Create private container
create_container("patient-container")
