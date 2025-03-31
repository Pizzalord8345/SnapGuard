### Security Audit Request for SnapGuard 🚨

Hello, security experts and fellow developers!  

SnapGuard is a Linux snapshot tool that requires superuser permissions. To ensure its security, I’d love to have a code audit from experienced contributors.  

#### 🔹 Why?  
- SnapGuard runs with `sudo`, making security crucial.  
- A vulnerability could lead to system compromise.  
- I want to implement best practices for security.  

#### 🔹 What needs review?  
- **Codebase:** Check for unsafe system calls, improper input validation, or privilege escalation risks.  
- **Permissions:** Should SnapGuard use Polkit or Linux Capabilities instead of full `sudo`?  
- **Best Practices:** Any recommendations to improve security?  

#### 🔹 How to help?  
- Clone the repository:  
  ```bash
  git clone https://github.com/Pizzalord8345/SnapGuard.git
  cd SnapGuard
  
- Review the code and submit issues or PRs for any vulnerabilities.

Thank you! Any help is greatly appreciated. 🙌
