# 🚀 AML Risk Assessment

## 📌 Table of Contents
- [Introduction](#introduction)
- [Demo](#demo)
- [What It Does](#what-it-does)
- [How We Built It](#how-we-built-it)
- [Challenges We Faced](#challenges-we-faced)
- [How to Run](#how-to-run)
- [Tech Stack](#tech-stack)
- [Team](#team)

---

## 🎯 Introduction
The main objective of this project is to develop a sophisticated AI/ML-powered system that automates entity research, verification, and risk scoring. By leveraging Generative AI, multi-source transaction data analysis, and automated workflows, we aim to enhance accuracy, reduce manual effort, and provide a robust risk evaluation framework. This solution will empower analysts with intelligent insights for informed decision-making.

## 🎥 Demo
🔗 [Live Demo](http://pradeep707.me:5173/) (if applicable)  
📹 [Video Demo](#) (if applicable)  
🖼️ Screenshots:

![Screenshot 1](link-to-image)

## ⚙️ What It Does
Our AML system will perform these steps automatically:

- **Entity Extraction**  
  The system identifies organizations, individuals, and jurisdictions from your transaction.

- **Sanctions Screening**  
  All entities are checked against global sanctions lists and PEP databases.

- **Entity Verification**  
  Organizations are verified through corporate registries and global databases.

- **Risk Assessment**  
  A comprehensive risk score is calculated based on all findings and evidence.

- **Report Generation**  
  A detailed risk report is generated with supporting evidence and recommendations.


## 🛠️ How We Built It
We utilized **Apache Airflow** for workflow orchestration, **Neo4j** for graph-based data modeling, and **Gemini LLMs** for AI-powered tasks like entity extraction and risk scoring. The frontend was built with React, Vite, and Mantine, while the **backend** used FastAPI for high performance and scalability.

## 🚧 Challenges We Faced
Key challenges included integrating diverse technologies (Airflow, Neo4j, Gemini), optimizing data pipelines for low latency, and designing an intuitive frontend. Overcoming these required innovative problem-solving, effective collaboration, and rapid iteration.

## 🏃 How to Run
### Prerequisites
- Ensure you have Docker and Docker Compose installed.
- For the frontend, ensure you have Node.js, npm, and yarn installed.

### Steps to Run the Project
1. **Clone the repository**  
   ```sh
   git clone https://github.com/ewfx/aidel-tech-vi-kings
   cd aidel-tech-vi-kings
   ```

2. **Set up the environment variables**  
   Navigate to the `src` directory and create a `.env` file by copying the `.env.example` file. Update the variables in the `.env` file as needed:  
   ```sh
   cd code/src
   cp .env.example .env
   ```

3. **Create the `src/data/pep` folder and copy the `pep_data.csv` file**  
   Create a folder named `pep` inside the `src/data` directory and copy the `pep_data.csv` file into it as root:  
   ```sh
   sudo mkdir -p data/pep
   sudo cp /path/to/pep_data.csv data/pep/
   ```

4. **Set up the backend**  
   Start the backend services using Docker Compose:  
   ```sh
   docker-compose up --build
   ```

5. **Set up the frontend**  
   - Navigate to the `client` directory.  
   - Replace the `API_URL` in the `constants.ts` and `transactionApi.ts` files with the appropriate backend API URL (e.g., `http://localhost:<backend-port>`).  
   - Install dependencies and start the development server:  
   ```sh
   cd client
   # Replace API_URL in constants.ts and transactionApi.ts
   nano code/src/client/src/api/constants.ts
   nano code/src/client/src/api/transactionApi.ts
   # Install dependencies and start the server
   yarn
   yarn dev
   ```

5. **Access the application**  
   - The backend API will be available at `http://localhost:8000`  
   - The Airflow UI will be available at `http://localhost:8080`.
   - The Neo4j UI will be available at `http://localhost:7474`.
   - The frontend will be available at `http://localhost:5173`.

### Steps to Run Tests
1. **Set up the testing environment**  
   Create a virtual environment and install the required dependencies:  
   ```sh
   cd code/test
   make setup
   ```

2. **Run all tests**  
   Execute all test suites (BDD, unit, and API tests):  
   ```sh
   make test-all
   ```

3. **Run specific tests**  
   - **BDD tests**:  
     ```sh
     make bdd
     ```
   - **Unit tests**:  
     ```sh
     make unit
     ```
   - **API tests**:  
     ```sh
     make api
     ```

4. **Generate a coverage report**  
   Create a test coverage report:  
   ```sh
   make report
   ```

5. **Clean up test artifacts**  
   Remove generated files and reports:  
   ```sh
   make clean
   ```

## 🏗️ Tech Stack
- 🔹 Frontend: React / Vite / Mantine
- 🔹 Backend: FastAPI
- 🔹 Database: Postgres / Redis
- 🔹 Other: Gemini API / Neo4j / Airflow

## 👥 Team
- **Indresh P** - [GitHub](https://github.com/indreshp135/) | [LinkedIn](https://www.linkedin.com/in/indresh-p-21b2581b6/)
- **Pradeep S** - [GitHub](https://github.com/pradeep-707) | [LinkedIn](https://www.linkedin.com/in/pradeep-s-769a4b123/)
- **Sailesh Swaminathan** - [GitHub](https://github.com/0149Sailesh) | [LinkedIn](https://www.linkedin.com/in/sailesh-swaminathan-9187161a2/)
- **Shri Hari L** - [GitHub](https://github.com/Shrihari10) | [LinkedIn](https://www.linkedin.com/in/shri-hari-l/)
- **Raja Kumar S** - [GitHub](https://github.com/theloganhugh/) | [LinkedIn](https://www.linkedin.com/in/s-raja-kumar-96ba29191/)
