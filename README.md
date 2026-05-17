
🛒 Olist E-Commerce ETL & Power BI Analytics Project

An end-to-end Data Engineering & Business Intelligence project built using the Brazilian Olist E-Commerce Dataset.

This project demonstrates a complete ETL pipeline using Python and Pandas, transforming raw transactional data into a clean Star Schema model ready for analytics and visualization in Power BI.

📌 Project Overview

The goal of this project is to:

Extract raw e-commerce datasets
Clean and transform the data
Build a Star Schema Data Warehouse model
Create analytical dashboards in Power BI
Generate business insights from sales, customers, logistics, and reviews
🏗 Architecture
Raw CSV Files
       ↓
Python ETL Pipeline
       ↓
Data Cleaning & Transformation
       ↓
Star Schema Data Warehouse
       ↓
Power BI Dashboard & Analytics
🛠 Tech Stack
Python
Pandas
Power BI
SQL
Docker
Kafka (optional)
Spark (optional)
📂 Dataset

Dataset used:

Olist Brazilian E-Commerce Dataset

Kaggle Link:
https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

📊 Star Schema Design
Fact Table
fact_order_items

Contains:

Order information
Product sales
Freight costs
Delivery metrics
Foreign keys to dimensions
Dimension Tables
dim_customer

Customer information:

City
State
ZIP code
dim_product

Product information:

Category
Dimensions
Weight
dim_seller

Seller information:

City
State
dim_payment

Payment details:

Payment type
Installments
dim_review

Customer reviews:

Review score
Review date
⚙️ ETL Pipeline

The ETL process includes:

1. Extract
Read raw CSV files using Pandas
2. Clean
Handle missing values
Remove duplicates
Convert data types
Parse datetime columns
3. Transform
Build dimension tables
Generate surrogate keys
Create fact table
Calculate business metrics
4. Load
Export clean star schema tables as CSV files
📈 Power BI Dashboard

The dashboard includes:

Executive Dashboard
Total Revenue
Total Orders
Average Order Value
Delivery Performance
Customer Analytics
Customer distribution
Top cities
Repeat customers
Product Analytics
Top categories
Best-selling products
Freight analysis
Logistics Dashboard
Delivery performance
Late deliveries
Shipping costs
Customer Reviews
Review score distribution
Delivery impact on ratings
📸 Dashboard Preview
Executive Dashboard

Add your dashboard screenshots here.

Customer Analytics

Add your dashboard screenshots here.

Product Analytics

Add your dashboard screenshots here.

🚀 How To Run
Clone Repository
git clone https://github.com/yourusername/olist-etl-powerbi-project.git
cd olist-etl-powerbi-project
Install Requirements
pip install -r requirements.txt
Run ETL Pipeline
python etl_pipeline.py
📁 Project Structure
olist-etl-powerbi-project/
│
├── data/
│   ├── raw/
│   └── processed/
│
├── notebooks/
│
├── scripts/
│   └── etl_pipeline.py
│
├── powerbi/
│   └── dashboard_screenshots/
│
├── sql/
│
├── README.md
├── .gitignore
📌 Key Business Insights
Delayed deliveries negatively impact customer review scores
Some product categories generate high revenue but also high freight costs
Certain states have significantly higher delivery times
Repeat customers contribute strongly to total revenue
🔥 Future Improvements
Real-time streaming using Kafka
Spark Structured Streaming integration
Airflow orchestration
PostgreSQL Data Warehouse
Automated reporting pipeline
