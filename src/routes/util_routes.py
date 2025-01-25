from sanic import Blueprint
from sanic.response import json
from sanic.request import Request
from src.utils.geocoding import geocode_address
from src.utils.responses import success_response, error_response

def setup_util_routes(blueprint: Blueprint) -> None:
    @blueprint.post("/utils/geocode")
    async def geocode_route(request: Request) -> json:
        """
        Geocode an address string to (longitude, latitude) coordinates
        
        Request body:
        {
            "address": "string"  // The address to geocode
        }
        """
        try:
            # Get address from request body
            address = request.json.get("address")
            if not address:
                return error_response(
                    message="Address is required",
                    error_code="MISSING_ADDRESS",
                    status=400
                )

            # Geocode the address
            coordinates = geocode_address(address)
            
            # Prepare response
            data = {
                "coordinates": coordinates,
                "address": address
            }
            
            if coordinates:
                return success_response(
                    data=data,
                    message="Address geocoded successfully"
                )
            else:
                return error_response(
                    message="Failed to geocode address",
                    error_code="GEOCODING_FAILED",
                    details={"address": address},
                    status=400
                )

        except Exception as e:
            return error_response(
                message="Internal server error during geocoding",
                error_code="GEOCODING_ERROR",
                details={"error": str(e)},
                status=500
            )
