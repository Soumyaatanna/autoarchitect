import React, { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

interface DiagramProps {
    chart: string;
}

const DiagramViewer: React.FC<DiagramProps> = ({ chart }) => {
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        mermaid.initialize({
            startOnLoad: true,
            theme: 'default',
            securityLevel: 'loose',
        });
    }, []);

    useEffect(() => {
        if (containerRef.current) {
            containerRef.current.innerHTML = ''; // Clear previous
            // Generate unique ID
            const id = `mermaid-${Math.random().toString(36).substr(2, 9)}`;
            try {
                mermaid.render(id, chart).then((result) => {
                    if (containerRef.current) {
                        containerRef.current.innerHTML = result.svg;
                    }
                });
            } catch (error) {
                console.error("Mermaid error:", error);
                if (containerRef.current) containerRef.current.innerHTML = "Error rendering diagram.";
            }
        }
    }, [chart]);

    return (
        <div className="w-full overflow-x-auto p-4 bg-white rounded-lg shadow border border-gray-200" ref={containerRef}>
            Loading Diagram...
        </div>
    );
};

export default DiagramViewer;
