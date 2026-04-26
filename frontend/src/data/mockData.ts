export type ExperimentStatus = "Pending" | "In Progress" | "Completed" | "Needs Review";

export interface Experiment {
  id: string;
  title: string;
  status: ExperimentStatus;
  domain: string;
  created: string;
  updated: string;
  duration: string;
  budget: number;
  optimizedBudget: number;
}

export const experiments: Experiment[] = [
  {
    id: "exp_001",
    title: "Probiotic X and Gut Permeability",
    status: "Completed",
    domain: "Gut Health",
    created: "2025-03-12",
    updated: "2025-04-18",
    duration: "8 weeks",
    budget: 12450,
    optimizedBudget: 8980,
  },
  {
    id: "exp_002",
    title: "Nano Particle Drug Delivery",
    status: "In Progress",
    domain: "Pharmacology",
    created: "2025-04-02",
    updated: "2025-04-22",
    duration: "12 weeks",
    budget: 28900,
    optimizedBudget: 21400,
  },
  {
    id: "exp_003",
    title: "CRISPR Gene Knockout Efficiency",
    status: "Needs Review",
    domain: "Genetics",
    created: "2025-04-10",
    updated: "2025-04-24",
    duration: "10 weeks",
    budget: 18750,
    optimizedBudget: 14200,
  },
  {
    id: "exp_004",
    title: "Anti-inflammatory Activity Test",
    status: "Completed",
    domain: "Immunology",
    created: "2025-02-20",
    updated: "2025-04-05",
    duration: "6 weeks",
    budget: 9200,
    optimizedBudget: 7150,
  },
];

export const workflowModules = [
  {
    num: 1,
    key: "literature",
    title: "Literature QC",
    description: "Check if similar work exists and find top references.",
    status: "Completed" as ExperimentStatus,
  },
  {
    num: 2,
    key: "plan",
    title: "Experiment Plan",
    description: "Generate complete protocol, materials, budget, timeline & validation.",
    status: "Completed" as ExperimentStatus,
  },
  {
    num: 3,
    key: "cost",
    title: "Cost Optimizer",
    description: "Optimize costs with alternative suppliers, quantities and strategies.",
    status: "In Progress" as ExperimentStatus,
  },
  {
    num: 4,
    key: "collab",
    title: "Collaboration Finder",
    description: "Find researchers working on similar projects.",
    status: "In Progress" as ExperimentStatus,
  },
  {
    num: 5,
    key: "review",
    title: "Scientist Review",
    description: "Get expert feedback and continuously improve.",
    status: "Pending" as ExperimentStatus,
  },
  {
    num: 6,
    key: "report",
    title: "Final Report",
    description: "Export a complete, ready-to-run experiment plan.",
    status: "Pending" as ExperimentStatus,
  },
];

export const collaborators = [
  {
    initials: "EM",
    name: "Dr. Elena Marquez",
    institution: "Stanford University",
    match: 92,
    topic: "Probiotic-mediated gut barrier function",
  },
  {
    initials: "RK",
    name: "Prof. Raj Kapoor",
    institution: "Johns Hopkins",
    match: 87,
    topic: "Microbiome inflammation pathways",
  },
  {
    initials: "AS",
    name: "Dr. Aiko Sato",
    institution: "MIT Biological Engineering",
    match: 81,
    topic: "Tight junction protein modulation",
  },
];

export const recentReviews = [
  { initials: "JC", rating: 4.8, summary: "Solid protocol; suggest larger control cohort." },
  { initials: "MR", rating: 4.5, summary: "Validation metrics are appropriate for this design." },
  { initials: "DV", rating: 4.6, summary: "Budget is reasonable, consider alternative supplier for reagents." },
];
