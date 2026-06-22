export interface FeatureItem {
  id: string;
  title: string;
  description: string;
}

export interface DishItem {
  id: string;
  name: string;
  description: string;
  priceEur: number;
  imagePath?: string;
  category?: string;
  badge?: string | null;
  weight?: string;
  allergens?: string[];
  extras?: string;
}

export interface NavItem {
  id: string;
  label: string;
  href: string;
}

export interface GalleryPhoto {
  id: string;
  title: string;
  path: string;
}

export interface ApplicationFormData {
  name: string;
  email: string;
  phone: string;
  department: string;
  experience: string;
  message: string;
}

export type ApplicationFormErrors = Partial<Record<keyof ApplicationFormData, string>>;
