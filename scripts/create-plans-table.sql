-- Create Plans table in public schema for API
CREATE TABLE IF NOT EXISTS public."Plans" (
    "Id" uuid NOT NULL PRIMARY KEY,
    "Name" text NOT NULL,
    "Description" text NOT NULL,
    "MonthlyPrice" numeric NOT NULL,
    "YearlyPrice" numeric NOT NULL,
    "MaxProducts" integer NOT NULL,
    "MaxOrdersPerMonth" integer NOT NULL,
    "MaxStorageGB" integer NOT NULL,
    "CustomDomainEnabled" boolean NOT NULL,
    "AdvancedAnalytics" boolean NOT NULL,
    "IsActive" boolean NOT NULL,
    "CreatedAt" timestamp with time zone NOT NULL,
    "UpdatedAt" timestamp with time zone NOT NULL
);

-- Insert default Free Plan if not exists
INSERT INTO public."Plans" (
    "Id", "Name", "Description", "MonthlyPrice", "YearlyPrice", 
    "MaxProducts", "MaxOrdersPerMonth", "MaxStorageGB", 
    "CustomDomainEnabled", "AdvancedAnalytics", "IsActive", 
    "CreatedAt", "UpdatedAt"
) VALUES (
    gen_random_uuid(), 
    'Free Plan', 
    'Free plan with basic features', 
    0, 0, 
    100, 1000, 1, 
    false, false, true, 
    NOW(), NOW()
) ON CONFLICT DO NOTHING;

