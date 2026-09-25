export interface DoctorProfile {
  id: string;
  name: string;
  email: string;
  role: 'doctor';
}

export interface AuthSession {
  token: string;
  doctor: DoctorProfile;
}
