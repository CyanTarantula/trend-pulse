"use client";

import dynamic from "next/dynamic";
import "swagger-ui-react/swagger-ui.css";
import spec from "@/lib/openapi.json";

// Dynamically import SwaggerUI to avoid server-side rendering issues
const SwaggerUI = dynamic(() => import("swagger-ui-react"), { ssr: false });

export default function SwaggerClient() {
    return (
        <div className="swagger-container">
            <SwaggerUI spec={spec} />
            <style jsx global>{`
        .swagger-container {
          background-color: white;
          padding: 20px;
          border-radius: 8px;
        }
        /* Custom dark mode adjustments if needed, 
           but usually SwaggerUI is best kept white/standard for readability */
      `}</style>
        </div>
    );
}
