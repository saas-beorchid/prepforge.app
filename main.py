from app import app

# Register adaptive API blueprint
try:
    from api_adaptive_endpoints import adaptive_api
    app.register_blueprint(adaptive_api)
    print("✅ Adaptive API blueprint registered")
except Exception as e:
    print(f"⚠️  Failed to register adaptive API: {e}")

# Register Stripe integration
try:
    from stripe_integration import register_stripe_routes
    register_stripe_routes(app)
    print("✅ Stripe integration registered")
except Exception as e:
    print(f"⚠️  Failed to register Stripe integration: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
