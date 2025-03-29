<?php
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // Get user input from the frontend
    $data = json_decode(file_get_contents('php://input'), true);
    $userQuestion = $data['question'];

    // Groq API endpoint and API Key
    $groqApiUrl = 'https://api.groq.com/v1/query';
    $groqApiKey = 'YOUR_GROQ_API_KEY';

    // Prepare the data to send to Groq
    $postData = json_encode([
        'query' => $userQuestion
    ]);

    // Initialize cURL to send the POST request to Groq
    $ch = curl_init($groqApiUrl);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Authorization: Bearer ' . $groqApiKey,
        'Content-Type: application/json'
    ]);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $postData);

    // Send the request to Groq and get the response
    $response = curl_exec($ch);
    curl_close($ch);

    // Parse the response
    $responseData = json_decode($response, true);

    // If there's an error or no result, send an error message
    if (isset($responseData['error'])) {
        echo json_encode(['error' => 'Sorry, something went wrong!']);
    } else {
        // Extract response message from Groq and send back to frontend
        $botReply = $responseData['response'] ?? 'Sorry, I didn\'t get that.';
        echo json_encode(['answer' => $botReply]);
    }
}
?>
