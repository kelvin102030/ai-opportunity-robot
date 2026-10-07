def create_build_plan(candidate, business_validation):
    """
    Turn a validated opportunity into a concrete MVP build and launch plan.
    """

    recommendation = business_validation.get("recommendation", "")
    signal = candidate.get("signal", "general")

    eligible = recommendation == "MVP BUILD APPROVED"

    if signal == "customer_service":
        product_type = "Customer-support platform"
        mvp_features = [
            "Customer complaint submission",
            "Complaint tracking",
            "Business support dashboard",
            "Status updates",
            "Basic analytics",
        ]
        screens = [
            "Welcome / Login",
            "Submit Complaint",
            "My Complaints",
            "Complaint Details",
            "Business Dashboard",
            "Settings",
        ]

    elif signal == "telecom_problems":
        product_type = "Telecom problem and complaint assistant"
        mvp_features = [
            "Network/problem reporting",
            "Complaint tracking",
            "Provider selection",
            "Status notifications",
            "Problem history",
        ]
        screens = [
            "Welcome / Login",
            "Report Problem",
            "My Reports",
            "Report Details",
            "Notifications",
            "Settings",
        ]

    elif signal == "small_business_operations":
        product_type = "Small-business operations assistant"
        mvp_features = [
            "Task tracking",
            "Customer records",
            "Sales/expense recording",
            "Business reminders",
            "Simple dashboard",
        ]
        screens = [
            "Welcome / Login",
            "Dashboard",
            "Customers",
            "Tasks",
            "Sales / Expenses",
            "Settings",
        ]

    elif signal == "business_costs":
        product_type = "Business cost management tool"
        mvp_features = [
            "Expense tracking",
            "Cost categories",
            "Spending reports",
            "Budget alerts",
            "Business dashboard",
        ]
        screens = [
            "Welcome / Login",
            "Dashboard",
            "Add Expense",
            "Reports",
            "Budgets",
            "Settings",
        ]

    else:
        product_type = "Problem-solving business application"
        mvp_features = [
            "User registration",
            "Core problem-solving workflow",
            "History",
            "Notifications",
            "Basic dashboard",
        ]
        screens = [
            "Welcome / Login",
            "Home",
            "Core Feature",
            "History",
            "Settings",
        ]

    return {
        "build_eligibility": (
            "MVP BUILD APPROVED"
            if eligible
            else "MVP BUILD NOT APPROVED"
        ),
        "product_type": product_type,
        "mvp_features": mvp_features,
        "screens": screens,
        "user_flow": [
            "User creates an account",
            "User enters the problem-solving workflow",
            "User submits or records the required information",
            "System stores and processes the information",
            "User receives a useful result or status update",
            "User returns to track progress or history",
        ],
        "technology": [
            "Mobile-friendly web application or Android app",
            "Python / Flask backend",
            "PostgreSQL database",
            "REST API",
            "Secure authentication",
            "Cloud deployment",
        ],
        "data_model": [
            "Users",
            "Problem reports / records",
            "Status history",
            "Notifications",
            "Payments or subscriptions",
        ],
        "build_phases": [
            "1. Define the exact MVP workflow",
            "2. Design the database",
            "3. Build the backend API",
            "4. Build the user interface",
            "5. Add authentication and security",
            "6. Connect database and API",
            "7. Test the complete user flow",
            "8. Deploy the MVP",
            "9. Collect real user feedback",
            "10. Improve before public launch",
        ],
        "testing_plan": [
            "Test registration and login",
            "Test the core workflow",
            "Test invalid input",
            "Test database persistence",
            "Test mobile screen sizes",
            "Test security and authentication",
            "Test failure and recovery cases",
            "Run a small real-user pilot",
        ],
        "play_store_preparation": [
            "Create Android application package",
            "Set application name and package ID",
            "Create app icon",
            "Prepare screenshots",
            "Write store description",
            "Prepare privacy policy",
            "Complete required app declarations",
            "Configure signing",
            "Build release version",
            "Test release build",
        ],
        "publishing_checklist": [
            "Google Play developer account",
            "Production Android build",
            "Signed release package",
            "Store listing",
            "Screenshots and graphics",
            "Privacy policy",
            "Content and data-safety declarations",
            "Final testing",
            "Submit for Google Play review",
        ],
        "monetization_launch": [
            "Choose the first paying customer",
            "Test the pricing hypothesis",
            "Offer the MVP to a small pilot group",
            "Measure usage and retention",
            "Collect willingness-to-pay feedback",
            "Convert successful pilots into paying customers",
        ],
    }
