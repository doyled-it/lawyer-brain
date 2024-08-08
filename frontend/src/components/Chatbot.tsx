import React, {
  useState,
  useEffect,
  useRef,
  ChangeEvent,
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
  Tooltip,
} from "@mui/material";
import { Speaker } from "../types/Speaker";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./Chatbot.css";

interface Message {
  sender: "user" | "bot";
  text: string;
  sources?: string[];
}

interface BackendResponse {
  message: string;
  sources?: string[];
  // Add other keys as needed
}

const Chatbot: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>("");
  const [selectedSpeaker, setSelectedSpeaker] = useState<Speaker | string>("");
  const [isTyping, setIsTyping] = useState<boolean>(false);
  const [initialLoadComplete, setInitialLoadComplete] =
    useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Load chat history from localStorage on mount
  useEffect(() => {
    const savedMessages = localStorage.getItem("chatMessages");
    if (savedMessages) {
      const parsedMessages: Message[] = JSON.parse(savedMessages);
      console.log("Loaded messages from localStorage:", parsedMessages);
      setMessages(parsedMessages);
    }
    setInitialLoadComplete(true);
  }, []);

  // Save chat history to localStorage whenever messages change after the initial load
  useEffect(() => {
    if (initialLoadComplete) {
      console.log("Saving messages to localStorage:", messages);
      localStorage.setItem("chatMessages", JSON.stringify(messages));
    }
  }, [messages, initialLoadComplete]);

  const sendMessage = async () => {
    if (input.trim() === "") return;

    const userMessage: Message = { sender: "user", text: input };
    setMessages((prevMessages) => [...prevMessages, userMessage]);
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
        sources: response.data.sources,
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

  const clearChatHistory = () => {
    setMessages([]);
    localStorage.removeItem("chatMessages");
  };

  useEffect(scrollToBottom, [messages]);

  return (
    <Box className="chat-container">
      <Paper elevation={3} className="chat-paper">
        <List className="chat-list">
          {messages.map((msg, index) => (
            <Box key={index} sx={{ marginBottom: "16px" }}>
              <ListItem
                className={`chat-bubble ${msg.sender}`}
                sx={{
                  display: "flex",
                  justifyContent:
                    msg.sender === "user" ? "flex-end" : "flex-start",
                }}
              >
                <Box className={`bubble-content ${msg.sender}`}>
                  <Typography variant="body1">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.text}
                    </ReactMarkdown>
                  </Typography>
                </Box>
              </ListItem>
              {msg.sources && msg.sources.length > 0 && (
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "flex-start",
                    gap: "4px",
                    marginTop: "-12px",
                    marginLeft: "16px",
                  }}
                >
                  {Array.from(new Set(msg.sources)).map((source, i) => (
                    <Tooltip key={i} title={source}>
                      <Button
                        variant="contained"
                        color="secondary"
                        size="small"
                        sx={{
                          minWidth: "24px",
                          padding: "4px",
                          borderRadius: "50%",
                          width: "24px",
                          height: "24px",
                          minHeight: "24px",
                        }}
                        onClick={() => window.open(source, "_blank")}
                      >
                        {i + 1}
                      </Button>
                    </Tooltip>
                  ))}
                </Box>
              )}
            </Box>
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
          sx={{ mt: 2 }}
        >
          Send
        </Button>
        <Button
          variant="outlined"
          color="secondary"
          onClick={clearChatHistory}
          className="clear-button"
          sx={{ mt: 2 }}
        >
          Clear Chat History
        </Button>
      </Paper>
    </Box>
  );
};

export default Chatbot;
