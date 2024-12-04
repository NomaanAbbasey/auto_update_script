from kubernetes import client, config, watch
import yaml
import os

OPENAPI_TEMPLATE = "openapi_template.yaml"
UPDATED_OPENAPI = "updated_openapi.yaml"

def load_kube_config():
    """Load Kubernetes configuration."""
    config.load_kube_config()

def fetch_services():
    """Fetch all services in the cluster."""
    v1 = client.CoreV1Api()
    services = v1.list_service_for_all_namespaces()
    return services.items

def generate_openapi_spec(services):
    """Generate an updated OpenAPI spec based on services."""
    # Load the OpenAPI template
    with open(OPENAPI_TEMPLATE, "r") as file:
        openapi_spec = yaml.safe_load(file)

    # Clear existing paths
    openapi_spec["paths"] = {}

    # Add new paths dynamically
    for service in services:
        name = service.metadata.name
        namespace = service.metadata.namespace
        ip = service.spec.cluster_ip or service.status.load_balancer.ingress[0].ip
        port = service.spec.ports[0].port if service.spec.ports else 80

        service_url = f"http://{ip}:{port}"
        openapi_spec["paths"][f"/{name}"] = {
            "get": {
                "x-google-backend": {
                    "address": service_url
                },
                "responses": {
                    "200": {
                        "description": f"Successful response from {name}"
                    }
                }
            }
        }

    # Save updated OpenAPI spec
    with open(UPDATED_OPENAPI, "w") as file:
        yaml.dump(openapi_spec, file)

    return UPDATED_OPENAPI

def update_api_gateway():
    """Update the API Gateway with the new OpenAPI spec."""
    # Replace with your API Gateway configuration
    api_id = "your-api-id"
    gateway_id = "your-gateway-id"
    region = "your-region"

    # Create a new API config
    os.system(f"gcloud api-gateway api-configs create new-config \
                --api={api_id} \
                --openapi-spec={UPDATED_OPENAPI} \
                --project=$(gcloud config get-value project)")

    # Deploy the new API config to the gateway
    os.system(f"gcloud api-gateway gateways update {gateway_id} \
                --api-config=new-config \
                --location={region} \
                --project=$(gcloud config get-value project)")

def watch_services():
    """Watch for service changes and update API Gateway."""
    v1 = client.CoreV1Api()
    watcher = watch.Watch()

    for event in watcher.stream(v1.list_service_for_all_namespaces):
        service = event["object"]
        if event["type"] in ["ADDED", "DELETED", "MODIFIED"]:
            print(f"Service {service.metadata.name} {event['type']}")
            services = fetch_services()
            generate_openapi_spec(services)
            update_api_gateway()

if __name__ == "__main__":
    load_kube_config()
    watch_services()