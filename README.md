# 📘 **D**ata **F**orensics **A**utomation **F**ramework (DFAF)

The **Data Forensics Automation Framework (DFAF)** enables you to build an automation cluster based on a **master–worker architecture**.  
You can define your own workflows using scripts and execute them across the cluster. Interaction and management are handled via a **web-based dashboard**.

DFAF is designed for use in **small digital forensics laboratories** that already have some basic infrastructure in place, such as:

1. Several machines  
2. A network connecting these machines  
3. A shared NAS containing acquired data  
4. Optionally, a database storing metadata about the data on the NAS  

All your workflows are already well-defined, but you don’t want to invest in expensive commercial automation software or dedicated hardware.  
This is where **DFAF** comes in — it allows you to transform your existing machines into a fully functional automation cluster **without spending a single dime!**

DFAF consists of two main components: the **Cluster** and the **Modules**.

---

## ⚙️ Cluster

The cluster provides the core infrastructure: it handles **communication between machines**, **database interaction**, **logging**, the **user interface**, and **thread management** for executing tasks.  

DFAF implements a **master–worker architecture**.  
This means there is a single **Master** program that manages a set of **Worker** programs.  
Typically, these workers are distributed across machines in your network, and each can perform specific types of tasks.

### 👑 Master

The **Master** program serves as the central communication hub of the cluster.  
Every Worker registers itself with the Master at startup.  
Once registered, the Master can assign tasks to Workers, which in turn report back their progress and results.

All of this can be observed and managed through a **web interface**, implemented as a Flask web server running on the Master node.

### ♟️ Worker

**Workers** are the programs that execute your tasks.  
Each Worker can handle one or more task types, depending on your configuration and available modules.

---

## 🧩 Modules

**Modules** extend the functionality of DFAF.  
The most important ones are **Task Modules**, which define and execute workflows.  
Each Task Module is essentially a script that implements a specific automated workflow — in other words, it defines what a *Task* is.

Currently, there are **no default modules** included.

---

## 🧠 Prerequisites

Before you begin, ensure that you have the following:

- `Python` version **3.12** or higher installed

---

## ⚙️ Installation

The following example demonstrates how to set up a **Master** and a **dummy Worker** running on the same machine.

```bash
# Clone the repository
git clone https://github.com/FynnZ-code/dfaf.git

# Navigate to the project directory
cd dfaf

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Navigate into the source directory
cd src

# Start the Master
python3 -m DFAutomationFramework --Master

# Start a dummy Worker in a new terminal
python3 -m DFAutomationFramework --Worker --Tasks "Dummy"
