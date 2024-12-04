from kubernetes import client, config, watch
import yaml
import os

# OpenAPI Template and Generated File
OPENAPI_TEMPLATE = "openapi_template.yaml"
UPDATED_OPENAPI = "updated_openapi.yaml"

# Kubernetes Configuration
config.load_incluster_config()
v1 = client.CoreV1Api()

def fetch_services():
    """Fetch all Kubernetes services."""
    return v1.list_service_for_all_namespaces()

def generate_openapi_spec(services):
    """Generate OpenAPI spec from service list."""
    # Load base OpenAPI template
    with open(OPENAPI_TEMPLATE, "r") as file:
        openapi_spec = yaml.safe_load(file)

    # Clear existing paths
    openapi_spec["paths"] = {}

    for svc in services.items:
        name = svc.metadata.name
        namespace = svc.metadata.namespace
        cluster_ip = svc.spec.cluster_ip or svc.status.load_balancer.ingress[0].ip
        port = svc.spec.ports[0].port if svc.spec.ports else 80

        service_url = f"http://{cluster_ip}:{port}"
        openapi_spec["paths"][f"/{name}"] = {
            "get": {
                "x-google-backend": {"address": service_url},
                "responses": {"200": {"description": f"Response from {name}"}},
            }
        }

    # Save the updated OpenAPI spec
    with open(UPDATED_OPENAPI, "w") as file:
        yaml.dump(openapi_spec, file)

    return UPDATED_OPENAPI

def update_api_gateway():
    """Update API Gateway with new configuration."""
    api_id = "your-api-id"
    gateway_id = "your-gateway-id"
    region = "your-region"

    # Create new API config
    os.system(f"gcloud api-gateway api-configs create new-config \
                --api={api_id} \
                --openapi-spec={UPDATED_OPENAPI} \
                --project=$(gcloud config get-value project)")

    # Deploy config to gateway
    os.system(f"gcloud api-gateway gateways update {gateway_id} \
                --api-config=new-config \
                --location={region} \
                --project=$(gcloud config get-value project)")

def watch_services():
    """Watch Kubernetes service events and update API Gateway."""
    watcher = watch.Watch()
    for event in watcher.stream(v1.list_service_for_all_namespaces):
        svc = event["object"]
        if event["type"] in ["ADDED", "DELETED"]:
            print(f"Service {svc.metadata.name} {event['type']}")
            services = fetch_services()
            generate_openapi_spec(services)
            update_api_gateway()

if __name__ == "__main__":
    watch_services()