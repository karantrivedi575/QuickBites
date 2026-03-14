@startuml
left to right direction

actor Customer
actor Admin

rectangle "Cafe Management System" {
    usecase "Register Account" as UC1
    usecase "Login" as UC2
    usecase "Browse Products" as UC3
    usecase "Place Order" as UC4
    usecase "Manage Products" as UC5
    usecase "View Order History" as UC6
    usecase "Generate Invoice" as UC7
}

Customer --> UC1
Customer --> UC2
Customer --> UC3
Customer --> UC4
Customer --> UC6

Admin --> UC2
Admin --> UC5
Admin --> UC6
Admin --> UC7

@enduml
