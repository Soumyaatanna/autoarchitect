import React from 'react';
import ReactMarkdown from 'react-markdown';

interface SummaryProps {
    content: string;
}

const SummaryViewer: React.FC<SummaryProps> = ({ content }) => {
    return (
        <div className="prose prose-slate max-w-none p-6 bg-white rounded-lg shadow border border-gray-200">
            <ReactMarkdown>{content}</ReactMarkdown>
        </div>
    );
};

export default SummaryViewer;
