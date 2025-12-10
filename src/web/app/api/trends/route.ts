import { NextResponse } from 'next/server';
import { TrendService } from '@/services/TrendService';
import { getApiKeys } from '@/lib/google_sheets';

export const dynamic = 'force-dynamic'; // Ensure this route is not statically cached

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const apiKey = request.headers.get('x-api-key') || searchParams.get('key');

    if (!apiKey) {
        return unauthorizedResponse(request);
    }

    const validKeys = await getApiKeys();

    if (!validKeys.includes(apiKey)) {
        return unauthorizedResponse(request);
    }

    // Fetch data
    const trends = await TrendService.getTrends();

    return NextResponse.json(trends);
}

function unauthorizedResponse(request: Request) {
    const accept = request.headers.get('accept') || '';

    // Check if browser request
    if (accept.includes('text/html')) {
        return new NextResponse(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>Unauthorized</title>
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <style>
            body { 
                background: #000; 
                color: #fff; 
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; 
                display: flex; 
                align-items: center; 
                justify-content: center; 
                height: 100vh; 
                margin: 0; 
                padding: 20px;
                text-align: center;
            }
            .container { 
                max-width: 500px;
                background: #111;
                padding: 40px;
                border-radius: 12px;
                border: 1px solid #333;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            }
            h1 { margin-bottom: 20px; font-size: 24px; color: #fff; }
            p { color: #a3a3a3; line-height: 1.5; margin-bottom: 20px; }
            a { color: #6366f1; text-decoration: none; font-weight: 500; }
            a:hover { text-decoration: underline; }
          </style>
        </head>
        <body>
          <div class="container">
            <h1>Access Denied</h1>
            <p>You need a valid API key to access this data.</p>
            <p>Please contact <a href="mailto:yasbh2002@gmail.com">yasbh2002@gmail.com</a> to request an API key.</p>
          </div>
        </body>
      </html>
    `, {
            status: 401,
            headers: { 'Content-Type': 'text/html' }
        });
    }

    return NextResponse.json({
        error: "Unauthorized",
        message: "Please contact yasbh2002@gmail.com for an API key."
    }, { status: 401 });
}
