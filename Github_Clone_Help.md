# 📥 GitHub Clone Help (Using CMD / Terminal)

This guide explains how to **clone a GitHub repository to your local system** using **Command Prompt (CMD)** or any terminal.

---

## ✅ Prerequisites

Before cloning a repository, make sure:

* **Git is installed** on your system
  Check by running:

  ```bash
  git --version
  ```
* You have a **GitHub repository URL** (HTTPS or SSH)

---

## 📌 Step 1: Open Command Prompt

* Press `Win + R`
* Type `cmd`
* Press **Enter**

Or open **Terminal / PowerShell**.

---

## 📌 Step 2: Navigate to Desired Folder

Choose the folder where you want the repository to be cloned.

Example:

```bash
cd Desktop
```

Or:

```bash
cd path\to\your\folder
```

---

## 📌 Step 3: Clone the Repository

Use the `git clone` command followed by the repository URL.

### 🔹 HTTPS Method (Most Common)

```bash
git clone https://github.com/username/repository-name.git
```

Example:

```bash
git clone https://github.com/Ayankhan79/Offline-AI-Study-Assistant-via-LLMs.git
```

---

### 🔹 SSH Method (Optional)

Requires SSH key setup.

```bash
git clone git@github.com:username/repository-name.git
```

---

## 📌 Step 4: Enter the Cloned Repository

After cloning completes:

```bash
cd repository-name
```

---

## 📂 What Happens After Cloning?

* A new folder is created with the **same name as the repo**
* All files, commits, and branches are downloaded
* The repo is automatically linked to the original GitHub repository (`origin`)

Check with:

```bash
git remote -v
```

---

## 🔁 Common Useful Commands After Cloning

Pull latest changes:

```bash
git pull
```

Check repository status:

```bash
git status
```

View branches:

```bash
git branch
```

---

## ❗ Common Errors & Fixes

### ❌ `git is not recognized`

➡️ Git is not installed or not added to PATH
✔️ Install Git from: [https://git-scm.com/](https://git-scm.com/)

---

### ❌ Permission denied (SSH)

➡️ SSH key not configured
✔️ Use HTTPS method instead or configure SSH keys

---

## ✅ Summary

* `git clone` is used to copy a GitHub repository locally
* Works via **CMD, PowerShell, or Terminal**
* HTTPS is easiest for beginners
* Cloned repo is ready for development immediately
