# 🎉 MyEventMemory

A complete system for mapping photos at events and delivering them securely to participants.  
Ensures attendees automatically receive their personal photos without manual sorting by the event owner.

---

## ℹ️ About

Many events face the problem where photos taken by photographers remain only with the event owner.  
Attendees often do not get copies of their own photos, and the event owner has no easy way to sort and deliver them.

This system solves the problem by providing:

- Event group creation and management  
- QR code access for participants  
- Facial recognition authentication  
- Automatic photo matching  
- Secure photo delivery via email  

Participants see only the photos they appear in, creating a personal event memory.

---

## 🔄 Project Flow

1. **Event Creation** 🏷️  
   Event owner creates a new event group and names it.  
2. **QR Code Distribution** 📱  
   A QR code is generated and shared with attendees.  
3. **Attendee Authentication** 👤  
   Participants scan the QR code and log in using facial recognition.  
4. **Photo Upload** 📷  
   Photographer uploads photos to the website/server.  
5. **Photo Matching** 🔍  
   The system detects faces in the photos and matches them to registered attendees.  
6. **Photo Delivery** ✉️  
   Each participant receives an email with only the photos they appear in.  
7. **Participant Access** 💻  
   Users can view/download their photos through the application.

---

## ✨ Features

- Create and manage event groups  
- QR code generation for attendee access  
- Facial recognition authentication (Dlib & CNN)  
- Automatic photo upload and face detection  
- Personalized photo emails for participants  
- User-friendly web interface  
- Secure storage of event photos

---

## 🧰 Technologies

- **Backend:** Python, FastAPI  
- **Facial Recognition:** Dlib, CNN  
- **Image Processing:** OpenCV  
- **Frontend:** React  
- **Database:** MongoDB  
- **Email Delivery:** SMTP / Email Service  

---

## 🛠 How It Works

1. Photographer uploads photos to the server through the web interface.  
2. The system detects faces in each photo.  
3. Faces are matched to registered attendees using facial recognition.  
4. Photos are securely stored on the server.  
5. Each participant receives an email containing only the photos they appear in.  
6. Participants can log in to the app to view and download their photos.

   
## 📷 Screenshots

### Welcome Screen


<img width="100" height="100" alt="image" src="https://github.com/user-attachments/assets/c7b7a4e3-4995-42f8-82d5-39b0bc3e11b6" />

### Register Screen
<img width="100" height="100" alt="צילום מסך 2025-11-30 232558" src="https://github.com/user-attachments/assets/b49accf6-2126-415f-b951-1bb7277478e2" />



### Role Selection Screen
<img width="100" height="100" alt="צילום מסך 2025-11-30 232748" src="https://github.com/user-attachments/assets/9432f277-e385-4b24-8239-806c3c93a7a0" />

### Manager Screen (Create Event) & QR Code Generation Screen

<img width="100" height="100" alt="צילום מסך 2025-11-30 232804" src="https://github.com/user-attachments/assets/42272c76-ab96-4f9d-91c6-66a9cd37091b" />
 
### Reference Image Selection Screen

<img width="100" height="100" alt="צילום מסך 2025-11-30 234021" src="https://github.com/user-attachments/assets/5cdbb8c0-3a8f-4b8a-8dbf-1fc0153fd2c7" />

### Join Event Screen

<img width="100" height="100" alt="צילום מסך 2025-11-30 233956" src="https://github.com/user-attachments/assets/425330a7-2eed-4603-80bd-3f52f6c6c371" />

### Upload Event Photos Screen

<img width="100" height="100" alt="צילום מסך 2025-11-30 233109" src="https://github.com/user-attachments/assets/02f9fd65-c5fa-45e6-986c-cd8813ccbf8e" />

### My Photos Download Screen
<img width="100" height="100" alt="צילום מסך 2025-11-30 233356" src="https://github.com/user-attachments/assets/0c9f5f3c-a8df-4823-9e51-5312b768df1e" />

<img width="100" height="100" alt="צילום מסך 2025-11-30 234219" src="https://github.com/user-attachments/assets/74e46a1c-5600-46f0-bad3-bbd4ba27e219" />

<img width="100" height="100" alt="צילום מסך 2025-11-30 234236" src="https://github.com/user-attachments/assets/57d5a788-c46c-42a3-8340-5a80325c27e8" />

---



