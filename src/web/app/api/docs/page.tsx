import SwaggerClient from "@/components/SwaggerClient";
import { Metadata } from "next";

export const metadata: Metadata = {
    title: "API Documentation | Trend Pulse",
    description: "API Reference for Trend Pulse",
};

export default function ApiDocsPage() {
    return (
        <div className="min-h-screen bg-neutral-900 p-8">
            <div className="max-w-7xl mx-auto">
                <SwaggerClient />
            </div>
        </div>
    );
}
