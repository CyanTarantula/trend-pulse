declare module 'swagger-ui-react' {
    import * as React from 'react';

    export interface SwaggerUIProps {
        spec?: any;
        url?: string;
        layout?: string;
        onComplete?: (system: any) => void;
        requestInterceptor?: (request: any) => any;
        responseInterceptor?: (response: any) => any;
        docExpansion?: "list" | "full" | "none";
        defaultModelExpandDepth?: number;
        plugins?: any[];
        supportedSubmitMethods?: string[];
    }

    class SwaggerUI extends React.Component<SwaggerUIProps> { }
    export default SwaggerUI;
}
