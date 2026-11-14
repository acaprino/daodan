import { initializeApp } from "firebase/app";
import { getFirestore } from "firebase/firestore";
import { getFunctions } from "firebase/functions";

const app = initializeApp({ projectId: "shop-demo", apiKey: import.meta.env.VITE_FIREBASE_API_KEY });

export const db = getFirestore(app);
export const functions = getFunctions(app);
