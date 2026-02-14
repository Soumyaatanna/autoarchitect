import axios from 'axios';

const API_BASE_URL = '/api';

export const analyzeRepo = async (repoUrl: string, token?: string) => {
    const response = await axios.post(`${API_BASE_URL}/analyze`, {
        repo_url: repoUrl,
        github_token: token,
    });
    return response.data;
};

export const getJobStatus = async (jobId: string) => {
    const response = await axios.get(`${API_BASE_URL}/jobs/${jobId}`);
    return response.data;
};
