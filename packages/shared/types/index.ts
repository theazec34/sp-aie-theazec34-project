/**
 * Shared base types for transversal Brasaland apps.
 * Domain entities for the TypeScript hito live in `src/types/models.ts`.
 */

export type Id = string;

export interface BaseEntity {
  id: Id;
  createdAt?: string;
  updatedAt?: string;
}
