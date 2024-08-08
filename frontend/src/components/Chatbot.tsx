import React, {
  useState,
  ChangeEvent,
  useEffect,
  useRef,
  KeyboardEvent,
} from "react";
import axios from "axios";
import {
  Box,
  TextField,
  Button,
  List,
  ListItem,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  Paper,
} from "@mui/material";
import { Speaker } from "../types/Speaker";
import "./Chatbot.css";

interface Message {
  sender: "user" | "bot";
  text: string;
}

interface BackendResponse {
  message: string;
  // Add other keys as needed
}

const Chatbot: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>("");
  const [selectedSpeaker, setSelectedSpeaker] = useState<Speaker | string>("");
  const [isTyping, setIsTyping] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const sendMessage = async () => {
    if (input.trim() === "") return;

    const userMessage: Message = { sender: "user", text: input };
    setMessages([...messages, userMessage]);
    setInput("");
    setIsTyping(true);

    try {
      const response = await axios.post<BackendResponse>(
        "http://localhost:8000/chat",
        { user_message: input, speaker: selectedSpeaker || null }
      );
      const botMessage: Message = {
        sender: "bot",
        text: response.data.message,
      };
      setMessages((prevMessages) => [...prevMessages, userMessage, botMessage]);
    } catch (error) {
      console.error("Error sending message", error);
    } finally {
      setIsTyping(false);
    }
  };

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value);
  };

  const handleSpeakerChange = (e: SelectChangeEvent<string>) => {
    setSelectedSpeaker(e.target.value);
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      sendMessage();
    }
  };

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  useEffect(scrollToBottom, [messages]);

  return (
    <Box className="chat-container">
      <Paper elevation={3} className="chat-paper">
        <List className="chat-list">
          {messages.map((msg, index) => (
            <ListItem
              key={index}
              className={`chat-bubble ${msg.sender}`}
              sx={{
                display: "flex",
                justifyContent:
                  msg.sender === "user" ? "flex-end" : "flex-start",
              }}
            >
              <Box className={`bubble-content ${msg.sender}`}>
                <Typography variant="body1">{msg.text}</Typography>
              </Box>
            </ListItem>
          ))}
          {isTyping && (
            <ListItem
              className="chat-bubble bot"
              sx={{ display: "flex", justifyContent: "flex-start" }}
            >
              <Box className="bubble-content bot typing-indicator">
                <div className="dot"></div>
                <div className="dot"></div>
                <div className="dot"></div>
              </Box>
            </ListItem>
          )}
          <div ref={messagesEndRef} />
        </List>
        <FormControl fullWidth sx={{ mt: 2 }}>
          <InputLabel id="speaker-select-label">Select Speaker</InputLabel>
          <Select
            labelId="speaker-select-label"
            value={selectedSpeaker}
            onChange={handleSpeakerChange}
            label="Select Speaker"
          >
            <MenuItem value="">None</MenuItem>
            {Object.values(Speaker).map((speaker) => (
              <MenuItem key={speaker} value={speaker}>
                {speaker}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <TextField
          fullWidth
          value={input}
          onChange={handleInputChange}
          onKeyPress={handleKeyPress}
          placeholder="Type your message..."
          sx={{ mt: 2 }}
        />
        <Button
          variant="contained"
          color="primary"
          onClick={sendMessage}
          className="send-button"
        >
          Send
        </Button>
      </Paper>
    </Box>
  );
};

export default Chatbot;
