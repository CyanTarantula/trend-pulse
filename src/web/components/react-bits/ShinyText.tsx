import React from 'react';
import { cn } from "@/lib/utils";

// Placeholder for ShinyText if fetch fails
// Simulates a shiny gradient animation
const ShinyText = ({ text, disabled = false, speed = 3, className = "" }: { text: string; disabled?: boolean; speed?: number; className?: string }) => {
    const animationDuration = `${speed}s`;

    return (
        <div
            className={cn(
                "text-[#b5b5b5a4] bg-clip-text inline-block",
                !disabled && "animate-shiny-text bg-gradient-to-r from-transparent via-white/80 via-50% to-transparent bg-[length:200%_100%]",
                className
            )}
            style={{
                animationDuration: animationDuration,
            }}
        >
            {text}
        </div>
    );
};

export default ShinyText;
